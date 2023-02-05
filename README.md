# Streamlit & Firebase サンプル

## Google Cloud services

```sh
gcloud services enable compute.googleapis.com run.googleapis.com \
    artifactregistry.googleapis.com secretmanager.googleapis.com \
    cloudbuild.googleapis.com
```

### Firebase Authentication

[認証を Firebase で](https://firebase.google.com/docs/auth)行います。

https://console.firebase.google.com/

1. "Authentication" の認証からメールアドレス / パスワードを有効化
2. "Authentication" の Users でユーザーを登録
3. "プロジェクトの設定" で確認できる内容を以下の形式で src/libs/config.py に保存

```sh
firebase = {
  "apiKey": "apiKey",
  "authDomain": "projectId.firebaseapp.com",
  "databaseURL": "https://databaseName.firebaseio.com",
  "storageBucket": "projectId.appspot.com"
}
```

### Cloud IAM

アプリケーションのためのサービス アカウントを作成します。

```sh
export project_id=$( gcloud config get-value project )
gcloud iam service-accounts create sa-app \
    --display-name "SA for the streamlit app" \
    --description "Service Account for the Streamlit application"
```

### Cloud Run

公開 URL を取得するため、サンプルアプリケーションをデプロイしておきます。

```sh
gcloud run deploy dev-svc --image gcr.io/cloudrun/hello --region "asia-northeast1" \
    --platform "managed" --cpu 1.0 --memory 256Mi --max-instances 1 \
    --allow-unauthenticated
gcloud run services add-iam-policy-binding dev-svc --region "asia-northeast1" \
    --member "allUsers" --role "roles/run.invoker"
```

## ローカル開発

### リポジトリのクローン

```sh
git clone https://github.com/pottava/streamlit-with-firebase.git
cd streamlit-with-firebase
```

### アプリケーションの依存解決と起動

```sh
pip install poetry
export GOOGLE_CLOUD_PROJECT=$( gcloud config get-value project )
gcloud auth application-default login
cd src
poetry install
poetry run streamlit run app.py
```

## CI / CD パイプライン

Artifact Registry にリポジトリを作成します。

```sh
gcloud artifacts repositories create my-apps \
    --repository-format docker --location asia-northeast1 \
    --description="Containerized applications"
```

### Cloud Build の場合

Secret Manager に Firebase の設定を保存します。

```sh
gcloud secrets create firebase-configs --replication-policy "automatic" \
    --data-file src/libs/config.py
```

Cloud Build に必要となる権限を付与します。

```sh
export project_id=$( gcloud config get-value project )
export project_number=$(gcloud projects describe ${project_id} \
    --format="value(projectNumber)")
gcloud projects add-iam-policy-binding "${project_id}" \
    --member "serviceAccount:${project_number}@cloudbuild.gserviceaccount.com" \
    --role "roles/run.developer"
gcloud secrets add-iam-policy-binding firebase-configs \
    --member "serviceAccount:${project_number}@cloudbuild.gserviceaccount.com" \
    --role "roles/secretmanager.secretAccessor"
gcloud iam service-accounts add-iam-policy-binding \
    sa-app@${project_id}.iam.gserviceaccount.com \
    --member "serviceAccount:${project_number}@cloudbuild.gserviceaccount.com" \
    --role "roles/iam.serviceAccountUser"
```

一度ローカルからビルドを起動してみて、それを Cloud Run にデプロイしてみましょう。

```sh
cd src
poetry export --without-hashes --format=requirements.txt > requirements.txt
gcloud builds submit \
    --pack "image=asia-northeast1-docker.pkg.dev/${project_id}/my-apps/streamlit" \
    .
gcloud run deploy dev-svc --region "asia-northeast1" \
    --image "asia-northeast1-docker.pkg.dev/${project_id}/my-apps/streamlit" \
    --service-account "sa-app@${project_id}.iam.gserviceaccount.com"
open "$( gcloud run services describe dev-svc --region "asia-northeast1" \
    --format 'value(status.url)')"
```

[Cloud Build コンソール](https://console.cloud.google.com/cloud-build/triggers)から、リポジトリの連携とトリガーを設定します。

- Cloud Run の dev-svc へのデプロイには deploy/cloudbuild-dev.yaml を指定します
- サービス アカウントは空欄のまま

### GitHub Actions または GitLab CI/CD の場合

CI ツールに渡すサービスアカウントを作ります。

```sh
export project_id=$( gcloud config get-value project )
gcloud iam service-accounts create sa-cicd \
    --display-name "SA for CI/CD" \
    --description "Service Account for CI/CD pipelines"
gcloud projects add-iam-policy-binding "${project_id}" \
    --member "serviceAccount:sa-cicd@${project_id}.iam.gserviceaccount.com" \
    --role "roles/viewer"
gcloud projects add-iam-policy-binding "${project_id}" \
    --member "serviceAccount:sa-cicd@${project_id}.iam.gserviceaccount.com" \
    --role "roles/run.admin"
gcloud projects add-iam-policy-binding "${project_id}" \
    --member "serviceAccount:sa-cicd@${project_id}.iam.gserviceaccount.com" \
    --role "roles/storage.admin"
gcloud projects add-iam-policy-binding "${project_id}" \
    --member "serviceAccount:sa-cicd@${project_id}.iam.gserviceaccount.com" \
    --role "roles/artifactregistry.writer"
gcloud projects add-iam-policy-binding "${project_id}" \
    --member "serviceAccount:sa-cicd@${project_id}.iam.gserviceaccount.com" \
    --role "roles/cloudbuild.builds.editor"
gcloud iam service-accounts add-iam-policy-binding \
    sa-app@${project_id}.iam.gserviceaccount.com \
    --member "serviceAccount:sa-cicd@${project_id}.iam.gserviceaccount.com" \
    --role "roles/iam.serviceAccountUser"
gcloud iam service-accounts keys create key.json \
    --iam-account "sa-cicd@${project_id}.iam.gserviceaccount.com"
cat key.json && rm -f key.json
```

GitHub プロジェクトの Secret に以下の値を設定します。

- GOOGLECLOUD_PROJECT: プロジェクト ID
- GOOGLECLOUD_SA_KEY: デプロイするためのサービス アカウント
- GOOGLECLOUD_FIREBASE: Firebase の設定 JSON（ダブル クオーテーションにはエスケープが必要）

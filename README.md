# Streamlit & Firebase サンプル

## Google Cloud services

```sh
gcloud services enable compute.googleapis.com run.googleapis.com \
    artifactregistry.googleapis.com secretmanager.googleapis.com \
    cloudbuild.googleapis.com iamcredentials.googleapis.com
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
gcloud projects add-iam-policy-binding "${project_id}" \
    --member "serviceAccount:sa-app@${project_id}.iam.gserviceaccount.com" \
    --role "roles/bigquery.jobUser"
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
cd src
gcloud auth application-default login
export GCLOUD_PROJECT=$( gcloud config get-value project )
pip install poetry
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
gcloud builds submit \
    --tag "asia-northeast1-docker.pkg.dev/${project_id}/my-apps/streamlit" .
gcloud run deploy dev-svc --region "asia-northeast1" \
    --image "asia-northeast1-docker.pkg.dev/${project_id}/my-apps/streamlit" \
    --service-account "sa-app@${project_id}.iam.gserviceaccount.com" \
    --set-env-vars GCLOUD_PROJECT=$( gcloud config get-value project )
open "$( gcloud run services describe dev-svc --region "asia-northeast1" \
    --format 'value(status.url)')"
```

[Cloud Build コンソール](https://console.cloud.google.com/cloud-build/triggers)から、リポジトリの連携とトリガーを設定します。

- Cloud Run の dev-svc へのデプロイには deploy/cloudbuild-dev.yaml を指定します
- サービス アカウントは空欄のまま

### GitHub Actions または GitLab CI/CD 共通

CI ツールで利用するサービスアカウントを作ります。

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
```

CI ツールと連携する Workload Identity の設定をします。

```sh
gcloud iam workload-identity-pools create "idpool-cicd" --location "global" \
    --display-name "Identity pool for CI/CD services"
idp_id=$( gcloud iam workload-identity-pools describe "idpool-cicd" \
    --location "global" --format "value(name)" )
```

### GitHub Actions の場合

```sh
repo=<org-id>/<repo-id>
gcloud iam workload-identity-pools providers create-oidc "idp-github" \
    --workload-identity-pool "idpool-cicd" --location "global" \
    --issuer-uri "https://token.actions.githubusercontent.com" \
    --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --display-name "Workload IdP for GitHub"
gcloud iam service-accounts add-iam-policy-binding \
    sa-cicd@${project_id}.iam.gserviceaccount.com \
    --member "principalSet://iam.googleapis.com/${idp_id}/attribute.user_login/chris" \
    --role "roles/iam.workloadIdentityUser"
gcloud iam workload-identity-pools providers describe "idp-github" \
    --workload-identity-pool "idpool-cicd" --location "global" \
    --format "value(name)"
```

プロジェクトの Actions secrets and variables に以下の値を設定します。

- GOOGLE_CLOUD_PROJECT: プロジェクト ID
- GOOGLE_CLOUD_WORKLOAD_IDP: Workload Identity の IdP ID
- GOOGLE_CLOUD_FIREBASE: Firebase の設定 JSON、ダブル クオーテーションにエスケープが必要です！！

### GitLab CI/CD の場合

```sh
repo=<org-id>/<repo-id>
gcloud iam workload-identity-pools providers create-oidc "idp-gitlab" \
    --workload-identity-pool "idpool-cicd" --location "global" \
    --issuer-uri "https://gitlab.com/" \
    --allowed-audiences "https://gitlab.com" \
    --attribute-mapping "google.subject=assertion.sub,attribute.project_path=assertion.project_path" \
    --display-name "Workload IdP for GitLab"
gcloud iam service-accounts add-iam-policy-binding \
    sa-cicd@${project_id}.iam.gserviceaccount.com \
    --member "principalSet://iam.googleapis.com/${idp_id}/attribute.project_path/${repo}" \
    --role "roles/iam.workloadIdentityUser"
gcloud iam workload-identity-pools providers describe "idp-gitlab" \
    --workload-identity-pool "idpool-cicd" --location "global" \
    --format "value(name)"
```

プロジェクトの CI/CD Variables に以下の値を設定します。

- GOOGLE_CLOUD_PROJECT: プロジェクト ID
- GOOGLE_CLOUD_WORKLOAD_IDP: Workload Identity の IdP ID
- GOOGLE_CLOUD_FIREBASE: Firebase の設定 JSON

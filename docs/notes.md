# Notes

All agents are called agent.py

## Flow

1. Prompt with image
2. code_extraction_agent - extract code from image and stores in `current_code`.
3. validation_agent - takes `current_code` and validates it using the `validate_spectrum_code` which wraps the `bas2tap` command, storing any errors in `validation_errors`.
4. debugging_agent - takes `current_code` and `validation_errors` and stores the fixed code in `current_code`.
5. tap_creation_agent - takes `current_code` and creates a TAP file using the `tap_creation` tool which also wraps the `bas2tap` command storing the file path in ``

## Deployment

* [Agent Starter Pack](https://github.com/GoogleCloudPlatform/agent-starter-pack)


## Bugs

- [X] display_name parameter is not supported in Gemini API - https://github.com/google/adk-python/issues/1182

## Service Account

# 1. Define variables for clarity (replace with your actual values)
SERVICE_ACCOUNT_NAME="retro-righter-sa"
SERVICE_ACCOUNT_DISPLAY_NAME="Service Account for Cloud Run with GCS Signed URL Access"
PROJECT_ID="speccy-appmod" # Replace with your GCP project ID
GCS_BUCKET_NAME="retro-righter-taps" # Replace with the name of your GCS bucket

# 2. Create the Service Account
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
    --display-name="${SERVICE_ACCOUNT_DISPLAY_NAME}" \
    --project=${PROJECT_ID}

# 3. Grant the Cloud Run Invoker role (for basic Cloud Run operation)
#    This role allows the Cloud Run service to be invoked.
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

# 4. Grant roles for Cloud Storage signed URL creation
#    To create signed URLs, the service account needs the permissions to do
#    whatever action the signed URL will grant. For example:
#
#    a) If the signed URL will allow *reading* objects (GET):
gcloud storage buckets add-iam-policy-binding gs://${GCS_BUCKET_NAME} \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"

#    b) If the signed URL will allow *uploading/creating* objects (PUT/POST):
gcloud storage buckets add-iam-policy-binding gs://${GCS_BUCKET_NAME} \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectCreator"

#    c) If the signed URL will allow *deleting* objects (DELETE):
gcloud storage buckets add-iam-policy-binding gs://${GCS_BUCKET_NAME} \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin" # This also covers create/view/delete

#    You might not need all of these. Choose the specific roles that align
#    with the *intended actions* of the signed URLs you will generate.
#    `roles/storage.objectViewer` is for reading, `roles/storage.objectCreator`
#    is for writing/uploading, and `roles/storage.objectAdmin` is for full
#    control over objects. Using the principle of least privilege, grant
#    only what's necessary.

# Optional: If your Cloud Run service also needs to list objects in the bucket,
# you might add:
# gcloud storage buckets add-iam-policy-binding gs://${GCS_BUCKET_NAME} \
#     --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
#     --role="roles/storage.legacyBucketReader"
# (Note: roles/storage.objectViewer typically grants storage.objects.list as well,
# but depending on exact use case, legacyBucketReader can be more explicit for bucket listing.)

# 5. (Important for Cloud Run to sign URLs with service account credentials)
#    The service account needs permission to sign blobs on its own behalf.
#    This is generally covered by `roles/iam.serviceAccountTokenCreator` on the
#    service account itself, but for *generating* signed URLs using client libraries
#    (which is typical in a Cloud Run service), the runtime service account often
#    implicitly has this. However, it's good practice to ensure the
#    `iam.serviceAccounts.signBlob` permission is available. This permission is
#    part of roles like `roles/iam.serviceAccountUser` or a custom role.
#    In most Cloud Run scenarios, if the service account is attached to the
#    Cloud Run service, it already has the necessary signing capabilities.
#    However, if you encounter issues, explicitly granting `roles/iam.serviceAccountTokenCreator`
#    to itself can sometimes resolve it, though it's less common for runtime.
#    It's more often granted to a *user* or another *service account* that *impersonates* this SA.

#    For the service account to sign URLs, it needs to be able to
#    "sign blobs" with its own keys. The `roles/iam.serviceAccountTokenCreator`
#    role, when granted on the *service account itself* to *itself*, implicitly
#    allows this.
gcloud iam service-accounts add-iam-policy-binding \
    ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountTokenCreator"
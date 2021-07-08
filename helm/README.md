# Organization

There exist 2 helm charts: backend2 and backend2-secrets. Backend2 provides the main setup for this repo while backend2-secrets is contains a part that we do not include in this repository and thus cannot be automated. While you do not need to do anything for backend2 except pushing to the correct branch, secrets need to be manually deployed. Do make sure that you deploy backend2-secrets **before** you apply changes of backend2. Pods do not automatically update their environment when a `ConfigMap` or `Secrets` resource changes.

The required values file can be found in our password storage. Copy its content to the backend2-secrets folder (e.g. helm/backend2-secrets/values.review.yaml). Next you can execute from the project root folder:
```bash
helm upgrade -n pleio2 -f helm/backend2-secrets/values.review.yaml backend2-review-secrets helm/backend2-secrets
```

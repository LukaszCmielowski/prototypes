# AutoML (Technology Preview)

**AutoML** on Red Hat OpenShift AI automates building and comparing machine learning models for **tabular data**. You provide a dataset and the target you want to predict; AutoML trains many model types, ranks them, and gives you a leaderboard so you can choose a model and optionally register or deploy it without writing training code. See [Example scenarios](#6-example-scenarios) for typical use cases and a step-by-step tutorial.

**Status:** Technology Preview — This feature is not yet supported with Red Hat production service level agreements (SLAs) and may change. It provides early access for testing and feedback.

---

## 1. About AutoML

### 1.1. What AutoML gives you

AutoML takes care of the full workflow so you can focus on your use case:
- **Automated data preprocessing** — Your tabular data (CSV in S3) is loaded, sampled and split into train and test sets.
- **Automated feature engineering and training** — AutoML trains many model types (neural networks, tree-based, linear) using [AutoGluon](https://github.com/autogluon/autogluon)’s ensembling (stacking and bagging), then selects the top performers and refits them on the full dataset for production-ready predictors.
- **Leaderboard** — You get an HTML leaderboard ranking all top models by the right metric for your task (e.g., accuracy or ROC-AUC for classification, R² for regression), so you can compare and pick the best model.
- **Trained models and notebook** — You receive the refitted model artifacts and a generated notebook to explore and use the best predictor. You can then register models in Model Registry or deploy them with KServe if you need serving.

You run AutoML programmatically via the pipelines API or using AI Pipelines UI; no custom training code is required.

### 1.2. What AutoML supports (Technology Preview)

In this preview, AutoML supports **classification** (binary and multiclass) and **regression** for tabular data. You specify the task type and the label column; AutoML handles the rest.

| Area | Support |
|------|--------|
| **Data format** | CSV (tabular) |
| **Data source** | S3-compatible object storage (via RHOAI Connections) |
| **Task types** | Classification (binary, multiclass), regression |
| **Training** | AutoGluon (ensembling: stacking, bagging); automatic model selection and refit on full data |
| **What you get** | Trained model artifacts, HTML leaderboard, generated notebook |
| **How you run it** | AI Pipelines UI, API (programmatic) |

You can register and serve the models AutoML produces using RHOAI Model Registry and KServe separately. **Not in scope:** Non-tabular data (e.g., images, text), traditional hyperparameter tuning as the primary method, unsupervised learning.


### 1.3. How it works under the hood

AutoML runs as a pipeline on Red Hat OpenShift AI, powered by AutoGluon and orchestrated by Kubeflow Pipelines. Your data is accessed securely via RHOAI Connections (S3 credentials stored as Kubernetes secrets). Model Registry and KServe are not part of the run; you use them separately to register or serve the models AutoML produces. For implementation details and the pipeline source, see [References](#10-references).

---

## 2. What you need to provide

To run AutoML, you provide where your data is and what to predict.

### Required input parameters

| Parameter | Description |
|-----------|-------------|
| **Data location** | An S3 connection (RHOAI Connections) and the bucket name and path (key) of your CSV file. AutoML uses the connection’s Kubernetes secret for credentials. |
| **Label column** | The name of the column you want to predict (target). |
| **Task type** | `binary` or `multiclass` for classification, or `regression` for regression. |


### Optional input parameters

| Parameter | Default | Description |
|-----------|--------|-------------|
| **top_n** | `3` | How many top models to refit on the full dataset (and appear on the leaderboard). |

---

## 3. What you get from a run

When an AutoML run completes, you get:

- **Leaderboard** — An HTML file ranking the top models by the right metric for your task (e.g., accuracy or ROC-AUC for classification, R² for regression). Use it to compare and choose the best model.
- **Trained models** — One artifact per top-N model, refitted on the full dataset and ready to use or deploy.
- **Notebooks** — A generated notebook to load and use the best predictor (predictions, evaluation, etc.).

Artifacts are stored in the artifact store configured for your run (e.g., S3 via your Pipeline Server). For exact artifact paths and layout, see the [pipeline reference](https://github.com/LukaszCmielowski/pipelines-components/tree/rhoai_automl/pipelines/training/automl/autogluon_tabular_training_pipeline).

---

## 4. Example scenarios

AutoML lets you tackle common tabular use cases by providing a CSV and the column to predict—no training code required. For example: predict which telecom customers will churn, which transactions are risky, or what value a property will sell for.

A typical scenario is **predicting customer churn**: you have a table of customers (contract details, usage, demographics) and a column indicating who left. AutoML trains multiple models to predict that column, then gives you a leaderboard so you can pick the best predictor and use it to flag at-risk customers or drive retention.

| Scenario | Your data | You predict | Outcome |
|----------|-----------|--------------|---------|
| **Customer churn** | Customer attributes, tenure, charges | Will the customer churn? (Yes/No) | Leaderboard + best model; use it to target retention. |
| **Fraud or risk** | Transaction or account features | Is it fraudulent / high risk? | Ranked models; deploy the best for real-time scoring. |
| **Regression** | Property or product features | Price, demand, or other numeric target | Best regression model and metrics (e.g. R²). |

To try this yourself, follow the [Tutorial: Predict the Customer Churn](#9-tutorial-predict-the-customer-churn): step-by-step with the Telco Customer Churn dataset on Red Hat OpenShift AI.

---

## 5. Prerequisites

- **Llama stack** set up — See [Llama stack setup](../../llamastack/SETUP.md) for installation and configuration.
- Red Hat OpenShift AI installed and accessible, with Kubeflow Pipelines available (see [References](#10-references) for version).
- A **data science project** and a **Pipeline Server** configured with object storage for runs and artifacts.
- An **S3 connection** (RHOAI Connections) for your training data so AutoML can read your CSV.


---

## 6. Running AutoML

You run AutoML by creating a pipeline run and providing your data location (connection, bucket, file path), label column, and task type. You can set how many top models to refit (`top_n`; default 3). Use the Kubeflow Pipelines API or RHOAI pipeline API to submit the run.

When the run finishes, open the run’s artifacts to get the leaderboard, trained models, and notebook. From there you can pick a model and, if needed, register it in Model Registry or deploy it with KServe (see [Deploying models on the single-model serving platform](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_cloud_service/1/html/deploying_models/deploying_models_on_the_single_model_serving_platform)).

---

## 7. Tutorial: Predict the Customer Churn

**Scenario:** You have (or download) the **Telco Customer Churn** dataset: one row per customer, with features like contract type, tenure, charges, and a **Churn** column (Yes/No). The goal is to train a model that predicts **Churn** so you can identify at-risk customers and use the best model from the leaderboard for retention or deployment.

This tutorial walks you through that end-to-end: create a project and workbench in Red Hat OpenShift AI, configure S3 connections for results and training data, add the AutoML pipeline and dataset, run AutoML with the right settings, and view the leaderboard to pick the best model.

### 7.1. Create a new project and workbench

1. Log in to Red Hat OpenShift AI.
2. From the OpenShift AI dashboard, go to **Data science projects** and create a new data science project (for example, `customer-churn-ml`).
3. In the project, create a **workbench** (notebook environment). Choose an image and resource size as needed. For full steps, see [Creating a project and workbench](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/2.8/html/getting_started_with_red_hat_openshift_ai_self-managed/creating-a-project-workbench_get-started) in the Red Hat OpenShift AI documentation.

### 7.2. Create the S3 connection for results storage

You need an S3-compatible connection for pipeline **results** (artifacts, leaderboard, etc.). Use this same connection when you configure the **Pipeline Server** for the project so that pipeline runs can read and write to the same bucket.

1. In your project, open the **Connections** tab and click **Add connection**.
2. Select **S3 compatible object storage** as the connection type.
3. Enter a unique **name** for the connection (for example, `automl-results-s3`). A resource name is generated automatically.
4. Fill in the connection details:
   - **Endpoint** — Your S3-compatible bucket endpoint (use the format required by your provider).
   - **Bucket** — Name of the bucket for pipeline results and Pipeline Server artifacts.
   - **Region** — Default region for your S3 account.
   - **Access key** — Access key ID for your S3 provider.
   - **Secret key** — Secret access key for your S3 account.
5. Click **Create**.

Use this connection when configuring the Pipeline Server (e.g., in **Pipeline runtimes** or project settings) so the server stores pipeline runs and artifacts in this bucket. For exact UI steps and endpoint formatting, see [Using connections](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/2.22/html/working_on_data_science_projects/using-connections_projects) and [Creating an S3 client](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/2.13/html/working_with_data_in_an_s3-compatible_object_store/creating-an-s3-client_s3) in the Red Hat OpenShift AI documentation.

### 7.3. Attach the connection to the workbench

1. Open your project and go to the **Workbenches** tab.
2. For the workbench you created, use the action menu (⋮) and choose **Edit** (or the equivalent option to modify the workbench).
3. In the workbench configuration, attach the **results** S3 connection you created in 7.2 so the workbench can access the same bucket (for example, to download leaderboard or artifacts later).
4. Save and, if prompted, restart the workbench so the connection is applied.

### 7.4. Create an S3 connection for training data

Create a second connection that points to the bucket where you will store the **training dataset** (Customer Churn CSV).

1. In the same project, go to **Connections** and click **Add connection**.
2. Select **S3 compatible object storage**.
3. Enter a unique name (for example, `customer-churn-data-s3`) and complete:
   - **Endpoint**, **Bucket**, **Region**, **Access key**, **Secret key** for the bucket you will use for training data.
4. Click **Create**.

Note the connection **name** (resource name); you will use it as `train_data_secret_name` when creating the pipeline run.

### 7.5. Upload the training dataset to S3

1. Download the Customer Churn dataset: [WA_FnUseC_TelcoCustomerChurn.csv](https://github.com/IBM/watsonx-ai-samples/blob/master/cloud/data/customer_churn/WA_FnUseC_TelcoCustomerChurn.csv) (from the IBM watsonx AI samples repository).
2. Upload the file to the S3 bucket configured in the **training data** connection (7.4). Place it in a path you will use as the object key (for example, `data/WA_FnUseC_TelcoCustomerChurn.csv` or just `WA_FnUseC_TelcoCustomerChurn.csv`).
3. Note the **bucket name** and the **object key** (path) of the file; you will need them for `train_data_bucket_name` and `train_data_file_key` in the pipeline run.

### 7.6. Add the AutoML pipeline as a Pipeline Definition

1. Get the compiled AutoML pipeline from the repository: [autogluon_tabular_training_pipeline](https://github.com/LukaszCmielowski/pipelines-components/tree/rhoai_automl/pipelines/training/automl/autogluon_tabular_training_pipeline) (branch `rhoai_automl`). Build or download the compiled pipeline (e.g., the pipeline YAML/IR).
2. In Red Hat OpenShift AI, go to **Pipelines** (or **Develop & Train** → **Pipelines**) for your project.
3. Upload the compiled pipeline as a new **Pipeline Definition** (or create a pipeline from the YAML), following [Managing AI pipelines](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.0/html/working_with_ai_pipelines/managing-ai-pipelines_ai-pipelines).

### 7.7. Run AutoML with the required inputs

1. From **Pipelines**, create a new **Pipeline Run** for the AutoML pipeline you added.
2. Set the run parameters as follows (see Section 4 for what each means):

   | Parameter | Value |
   |-----------|--------|
   | **train_data_secret_name** | The connection (resource) name you created for training data in step 7.4 |
   | **train_data_bucket_name** | The bucket name where you uploaded the CSV in step 7.5 |
   | **train_data_file_key** | The object key (path) of the file, e.g. `data/WA_FnUseC_TelcoCustomerChurn.csv` or `WA_FnUseC_TelcoCustomerChurn.csv` |
   | **label_column** | `Churn` |
   | **task_type** | `binary` |
   | **top_n** (optional) | `3` (default) or another positive integer |

   If the UI asks for an experiment or run name (e.g. “Customer Churn”, “Customer Churn Prediction”), set them as run metadata; AutoML uses the parameters in the table above.

3. Ensure the Pipeline Server is configured with the results S3 connection from 7.2 so artifacts are stored in the expected bucket.
4. Start the run and wait for it to complete.

### 7.8. View the leaderboard

After the run has completed successfully:

1. Open the run details and go to **Artifacts** (or the artifact store configured for the run).
2. Locate the **leaderboard** artifact (e.g., an HTML file in the leaderboard-evaluation output).
3. Download or open the HTML leaderboard to compare the ranked models and their metrics.

For exact artifact paths and layout, see the pipeline reference below.

### 7.9. Predictor Notebook
TODO

### 7.10. Model Registry
TODO


### 7.11. Model Deployment (KServe — Autogluon ensemble on Red Hat OpenShift AI)

This section describes how to deploy an Autogluon ensemble on the cluster using KServe. You can obtain the serving image in one of two ways; both paths then converge to creating a **Serving Runtime** and deploying the model.

**Flow overview**

- **Path A:** Build the Docker image locally and push it to a container registry (e.g. Quay). *(Steps described below.)*
- **Path B:** Build the image directly on the cluster using OpenShift ImageStream and BuildConfig. *(Steps described below.)*

Once the image is available in a registry or on cluster (from Path A or Path B), the steps are the same: **Prepare ServingRuntime YAML** (use the Quay variant or the cluster-built variant) → **create Serving Runtime on the cluster** → **add image-pull credentials** (skip for Path B) → **create a deployment** with your Autogluon model (e.g. from S3).

---

#### Path A: Build image locally and push to a container registry

**Prerequisite: KServe repository**

To build the image you need the repository that contains the Dockerfile and the directories copied into the image (`kserve`, `storage`, `autogluonserver`, `third_party`, and related files). Clone the repository:

```bash
git clone https://github.com/LukaszCmielowski/kserve
cd kserve
```

The Dockerfile is located at `python/autogluon.Dockerfile`; the build must be run from the **repository root** so that the `COPY` instructions can find the `kserve`, `storage`, `autogluonserver`, and `third_party` directories.

**Dockerfile reference**

Build the image from a Dockerfile like the following (it is available in the cloned repo as `python/autogluon.Dockerfile`). It uses Python 3.11, installs KServe and storage dependencies, then the Autogluon server. Use it in the build command in step 1.

```dockerfile
ARG PYTHON_VERSION=3.11
ARG BASE_IMAGE=python:${PYTHON_VERSION}-slim-bookworm
ARG VENV_PATH=/prod_venv

FROM ${BASE_IMAGE} AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends python3-dev curl build-essential && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv

# Create virtual environment
ARG VENV_PATH
ENV VIRTUAL_ENV=${VENV_PATH}
RUN uv venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# ========== Install kserve dependencies ==========
COPY kserve/pyproject.toml kserve/uv.lock kserve/
RUN cd kserve && uv sync --active --no-cache

COPY kserve kserve
RUN cd kserve && uv sync --active --no-cache

# ========== Install kserve storage dependencies ==========
COPY storage/pyproject.toml storage/uv.lock storage/
RUN cd storage && uv sync --active --no-cache

COPY storage storage
RUN cd storage && uv pip install . --no-cache

# ========== Install autogluonserver dependencies ==========
COPY autogluonserver/pyproject.toml autogluonserver/
RUN cd autogluonserver && uv sync --active --no-cache

COPY autogluonserver autogluonserver
RUN cd autogluonserver && uv sync --active --no-cache

# Generate third-party licenses
COPY pyproject.toml pyproject.toml
COPY third_party/pip-licenses.py pip-licenses.py
# TODO: Remove this when upgrading to python 3.11+
RUN pip install --no-cache-dir tomli
RUN mkdir -p third_party/library && python3 pip-licenses.py

# =================== Final stage ===================
FROM ${BASE_IMAGE} AS prod

COPY third_party third_party

# Activate virtual env
ARG VENV_PATH
ENV VIRTUAL_ENV=${VENV_PATH}
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN useradd kserve -m -u 1000 -d /home/kserve

COPY --from=builder --chown=kserve:kserve third_party third_party
COPY --from=builder --chown=kserve:kserve $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=builder kserve kserve
COPY --from=builder storage storage
COPY --from=builder autogluonserver autogluonserver

USER 1000
ENV PYTHONPATH=/autogluonserver
ENTRYPOINT ["python", "-m", "autogluonserver"]
```

1. **Build the Docker image** from the root of the cloned [KServe repository](https://github.com/LukaszCmielowski/kserve) (where `python/autogluon.Dockerfile` and the `kserve`, `storage`, and `autogluonserver` directories exist). Use `-t` with the full image URL so you can push without a separate tag step. Run:

   ```bash
   nerdctl -n k8s.io build -f python/autogluon.Dockerfile -t quay.io/<YOUR_QUAY_USERNAME>/kserve-autogluonserver:latest .
   ```

   Replace `quay.io/<YOUR_QUAY_USERNAME>/kserve-autogluonserver:latest` with your registry and image name. Alternatively, use `docker build` with the same `-f` and `-t` values.

2. **Push the image** to your container registry:

   ```bash
   nerdctl -n k8s.io push quay.io/<YOUR_QUAY_USERNAME>/kserve-autogluonserver:latest
   ```

   Use the same image URL in the ServingRuntime YAML in the next section (`PATH_TO_YOUR_QUAY_IMAGE`).

#### Path B: Build image directly on Red Hat OpenShift AI

When you build the image on the cluster instead of pulling it from Quay, use the OpenShift Builds flow and then a Serving Runtime that points to the internal image registry. Use the same project/namespace for the build and for the Serving Runtime (e.g. `automl-project`).

**1. Create ImageStream**

1. In the OpenShift console, left side: **Builds** → **ImageStreams** → **Create ImageStream**.
2. Paste the following YAML and click **Create**:

```yaml
apiVersion: image.openshift.io/v1
kind: ImageStream
metadata:
  name: autogluonkserveimagev1
```

**2. Create BuildConfig**

1. In the console, left side: **Builds** → **BuildConfigs** → **Create BuildConfig** → **YAML View**.
2. Paste the following and click **Create**:

```yaml
apiVersion: build.openshift.io/v1
kind: BuildConfig
metadata:
  name: autogluonkserveimagev1
spec:
  source:
    type: Git
    git:
      uri: https://github.com/LukaszCmielowski/kserve
      ref: dev-autogluon-server
    contextDir: python
  strategy:
    type: Docker
    dockerStrategy:
      dockerfilePath: autogluon.Dockerfile
  output:
    to:
      kind: ImageStreamTag
      name: autogluonkserveimagev1:latest
  triggers:
    - type: ConfigChange
```

OpenShift will start a build. Wait for the build to complete (e.g. in **Builds** → **Builds**). The image will be available in the internal registry as `image-registry.openshift-image-registry.svc:5000/<namespace>/autogluonkserveimagev1:latest` (use your project namespace, e.g. `automl-project`).

After the image is built, follow the **Common steps** below; for Path B use the **Serving Runtime YAML for cluster-built image** and you can skip adding image-pull credentials for that image.

---

#### Common steps (after the image is in a registry or built on cluster)

The following steps apply whether the image was built locally (Path A) or on OpenShift (Path B). Start with **Prepare ServingRuntime YAML**.

##### Prepare ServingRuntime YAML

Create a YAML file for the KServe Serving Runtime. Set `metadata.namespace` to your project (e.g. `automl-project`). Set `image` according to how you obtained the image:

- **Path A (Quay):** `quay.io/<YOUR_QUAY_USERNAME>/kserve-autogluonserver:latest`
- **Path B (build on cluster):** `image-registry.openshift-image-registry.svc:5000/<namespace>/autogluonkserveimagev1:latest` (use the same namespace as above)

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: kserve-autogluonserver
  namespace: automl-project
spec:
  annotations:
    prometheus.kserve.io/port: "8080"
    prometheus.kserve.io/path: "/metrics"
  supportedModelFormats:
    - name: autogluon
      version: "1"
      autoSelect: true
      priority: 2
  protocolVersions:
    - v1
    - v2
  containers:
    - name: kserve-container
      image: {SERVING_IMAGE}
      args:
        - --model_name=autogluon
        - --model_dir=/mnt/models
        - --http_port=8080
      securityContext:
        allowPrivilegeEscalation: false
        privileged: false
        runAsNonRoot: true
        capabilities:
          drop:
            - ALL
      resources:
        requests:
          cpu: "1"
          memory: 2Gi
        limits:
          cpu: "1"
          memory: 2Gi
```

Replace `{SERVING_IMAGE}` and, if needed, `automl-project` with the values for your scenario (see list above).

##### Create the Serving Runtime on OpenShift

1. Log in to the Red Hat OpenShift AI cluster.
2. In the left menu: **Settings** → **Model resources and operations** → **Serving runtimes** → **Add serving runtime** → **Upload files**.
3. Upload the ServingRuntime YAML you prepared (with `image` and `namespace` set for your scenario).
4. In **Select the API protocol this runtime supports**, choose **REST**.
5. In **Select the model types this runtime supports**, select **Predictive model**.
6. Click **Create**.

##### Add credentials so the cluster can pull the image

*If you used Path B (image built on the cluster in the same project), the image is in the internal registry and you can skip this step.*

1. Log in to the Red Hat OpenShift Console.
2. Go to **Workloads** → **Secrets** → **Create** → **Image pull secret**.
3. Enter a secret name and copy it for the next step.
4. Ensure you are logged in to your image registry (e.g. Quay) so the secret can be used to pull the image.

Then attach the secret to the service account used by the runtime:

1. In the console: **User Management** → **ServiceAccounts** (choose the correct namespace).
2. Open the **builder** service account → **YAML**.
3. Under `imagePullSecrets`, add an entry with the secret name you created (e.g. `name: your-image-pull-secret-name`).

##### Create the deployment with your Autogluon ensemble

This assumes your Autogluon model (e.g. from an AutoML run) is stored in S3.

1. In the left menu: **AI hub** → **Deployments** → **Deploy model**.
2. Under **Model location**, choose **S3 object storage**.
3. Create a new connection or use an existing one and fill in the S3 credentials and path to the model.
4. Fill in all required fields (bucket, path, etc.).
5. For **Model type**, choose **Predictive model**.
6. Click **Next**.
7. Under **Model framework**, select **autogluon - 1**.
8. Under **Serving runtime**, choose **Select from list…** → **kserve-autogluonserver**.
9. Click **Next** → **Deploy model**.

After the deployment is created, you can use the deployed endpoint for inference. For more on serving and APIs, see [Deploying models on the single-model serving platform](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_cloud_service/1/html/deploying_models/deploying_models_on_the_single_model_serving_platform).

---

## References

- [KServe (LukaszCmielowski/kserve)](https://github.com/LukaszCmielowski/kserve) — repository containing the Dockerfile (`python/autogluon.Dockerfile`) and directories (`kserve`, `storage`, `autogluonserver`, `third_party`) required to build the Autogluon serving image for Model Deployment (Section 7.11)
- [AutoGluon](https://github.com/autogluon/autogluon) — AutoML engine used for training and ensembling
- [Deploying models on the single-model serving platform (Red Hat OpenShift AI)](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_cloud_service/1/html/deploying_models/deploying_models_on_the_single_model_serving_platform) — register and serve models after AutoML
- [AutoGluon tabular training pipeline (pipelines-components, branch rhoai_automl)](https://github.com/LukaszCmielowski/pipelines-components/tree/rhoai_automl/pipelines/training/automl/autogluon_tabular_training_pipeline) — implementation reference (pipeline source, parameters, KFP version)

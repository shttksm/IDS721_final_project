# IDS721 Final Project

Build a containerized or PaaS machine learning prediction model and deploy it in a scalable, and elastic platform:

* Team members: Sangjyh Lin, Tzu-Chun Hsieh, and Shota Takeshima
* We implemented a flask application that performs ML (Random forest) training and its prediction on GCP.
* Our flask application makes a prediction of whether the income is over 50K based on [Census Income Data Set](https://archive.ics.uci.edu/ml/datasets/Census+Income) put on Cloud Storage.
* We also deployed this app on Kubernetes cluster and evaluate its response with Locust load testing. 

Below are the steps of how to build and deploy this app.

## Preparing the dataset
* Copy the modified dataset from public Google Cloud bucket

```sh
BUCKET_NAME=YOUR_BUCKET_NAME
REGION="us-central1"
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
```
Create a bucket and set it as a shell variable, `BUCKET_NAME`.

```
TRAINING_DATA_SOURCE=gs://cloud-samples-data/ai-platform/census/algorithms/data/train.csv
TRAINING_DATA_PATH=gs://$BUCKET_NAME/algorithms-demo/data/train.csv
gsutil cp $TRAINING_DATA_SOURCE $TRAINING_DATA_PATH
```
Then, we can copy the modified dataset located on public Cloud Storage into our own buckets.

* Change the path of the dataset in the application code
Modify [this part](https://github.com/shttksm/IDS721_final_project/blob/master/main.py#L11-L12) in main.py

## Containerizing an application 

* Clone this repository and create a virtual environment 

```sh
git clone https://github.com/shttksm/IDS721_final_project

python3 -m venv ~/.IDS721_final_project
source ~/.IDS721_final_project/bin/activate

PROJECT_ID=YOUR_PROJECT_ID
```

* Run locally

```sh
make install
python main.py
```

You can access http://localhost:5000 to see the top page. If you access http://localhost:5000/train, the random forest model is trained In /predict page, the trained model makes a prediction using a subset of the training data.

* Create an image

```sh
docker build -f Dockerfile -t gcr.io/${PROJECT_ID}/rf-python:latest .
docker image ls
```

Now the application is containerized. In the Docker file, we designate the exposed port for the request. Also, the image name needs to include gcr.io, and the project name to register Container Registry (explained later).

* Running in Docker

```
docker run --rm -p 5001:5000 gcr.io/${PROJECT_ID}/rf-python
```

Run the above command to have Docker run the application in a container and map it to port 5001. Similar to "Run locally", can confirm the app's behavior via http://localhost:5001.

## Deploying a containerized web application

* Pushing the docker image to Container Registry

```sh
gcloud services enable containerregistry.googleapis.com
gcloud auth configure-docker
docker push gcr.io/${PROJECT_ID}/rf-python:latest
```

Push the Docker image that you just built to Container Registry after enabling the service and getting authentication.

* Creating a GKE cluster

```sh
gcloud config set compute/zone us-west2-a
gcloud services enable container.googleapis.com
gcloud container clusters create rf-cluster
```

First, set a zone in which we create Kubernetes cluster. Then create a cluster named `rf-cluster`.

```sh
kubectl get nodes
```

After the command completes, run the following command to see the cluster's three Nodes.

* Deploying the sample app to GKE

```sh
gcloud container clusters get-credentials rf-cluster --zone us-west2-a
kubectl create deployment rf-python --image=gcr.io/${PROJECT_ID}/rf-python:latest
kubectl scale deployment rf-python --replicas=3
kubectl autoscale deployment rf-python --cpu-percent=80 --min=1 --max=5
```

1. Ensure that you are connected to your GKE cluster.
2. Create a Kubernetes Deployment for your `rf-python` Docker image.
3. Set the baseline number of Deployment replicas to 3.
4. Create a `HorizontalPodAutoscaler` resource for your Deployment.

* Exposing the sample app to the internet

```sh
kubectl expose deployment rf-python --name=rf-python-service --type=LoadBalancer --port 80 --target-port 5000
kubectl get service
```

1. `--port` indicates the port to access the Load Balancer, and the actual cotainerized flask app uses 5000 as its exposed port. So, `--target-port` is 5000.
2. Run the following command to get the Service details for `rf-python-service`. See the `EXTERNAL_IP`.

## Autoscaler not working

But sometimes we can find the Autoscaler does not work.

![image](https://user-images.githubusercontent.com/52944419/116625091-ed846080-a8fd-11eb-812d-42a5a7b37d5c.png)

This may because the metric sensing function gets some problem. In this situation, we need to manually set up the metric sensing for Autoscaler:

* Apply metrics-server (you can find more info here: [https://github.com/kubernetes-sigs/metrics-server/releases](https://github.com/kubernetes-sigs/metrics-server/releases))

```sh
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.4.0/components.yaml
```

* Change the resource setting in yaml (under spec-template-spec-containers-resources add requests: cpu: 200m) as shown in the following picture.

![image](https://user-images.githubusercontent.com/52944419/116625258-33412900-a8fe-11eb-89b4-b0da26186cbf.png)

After change the yaml setting, you will find the autoscaler status is OK.

![image](https://user-images.githubusercontent.com/52944419/116625346-51a72480-a8fe-11eb-9da2-8de0a8dc70a8.png)

Once you see this status, you are good to deploy load test with autoscaler.



## Load testing

* Load testing with Locust

```sh
locust
```

In the directory that includes locustfile.py, type `locust` to invoke the website for load test setting and viewer.

* In the Locust webpage, set the number of users and their hatch rate. The below image shows the total response times and number of users over the load testing period.

![image](https://user-images.githubusercontent.com/56372825/116203564-d2e99600-a709-11eb-9a0c-86612c21f0a5.png)


* Pods scale up

After the load test, you can find the number of pods increase to 5 pods, which is the maximum setting in this project.

![image](https://user-images.githubusercontent.com/52944419/116625385-62579a80-a8fe-11eb-873e-42f8a66ec224.png)

In the locust UI, you can see when the user is 3604, we have some failure, since the request load is high and when the new pods is starting, we got some failures. After we got too many request, the system just cannot handle since it already autoscaled up to the maximum number of pods we set.

![image](https://user-images.githubusercontent.com/52944419/116625426-73a0a700-a8fe-11eb-9a76-a9e6832d401d.png)

* Use command line to check the result of load test

Run the following command can check autoscaler metric status

```sh
kubectl get hpa
```

In the beginning, we can see the target, which is cpu, is 0.

![image](https://user-images.githubusercontent.com/52944419/116625458-7ef3d280-a8fe-11eb-8f37-b32304d0ee94.png)

After running locust for a while, you can find the total cpu is around 200 percent, which is 4 times our autoscaling threshold.

![image](https://user-images.githubusercontent.com/52944419/116625469-87e4a400-a8fe-11eb-8058-2af893cc6991.png)

## I don't want to pay.

* Cleaning up
  * **Delete the Service:** This deallocates the Cloud Load Balancer created for your Service
  * **Delete the cluster:** This deletes the resources that make up the cluster, such as the compute instances, disks, and network resources

```sh
kubectl delete service rf-python-service
gcloud container clusters delete rf-cluster --zone us-west2-a 
```

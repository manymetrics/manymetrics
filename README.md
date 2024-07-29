# ManyMetrics

ManyMetrics is an open-source event tracking infrastructure:

- API based on AWS API Gateway and lambda
- Storage in AWS S3 in the [Apache Iceberg](https://iceberg.apache.org/) format
- SQL access to data via AWS Athena
- A JS client library

## Components

![Components](docs/components.png)

## Deployment

ManyMetrics uses terraform for setting up resources in an AWS account. The following comment will
- Create ECR repositories
- Build and upload docker images
- Create AWS resources

```
cd sample
terraform apply
```

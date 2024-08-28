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

## Approximate monthly cost of running

The calculations below do not include S3 storage and a few others costs like network costs but they should be relatively small.

| Service | Cost | 1kk events | 10kk events | 100kk events |
| ------- | ---- | ------- | -------- | --------- |
| API Gateway | $1 per 1kk req | $1 | $10 | $100 |
| Lambda | $0.0000000167 per ms <sup>[1]</sup> | $0.10 | $1 | $10 |
| Kinesis | $0.015 per hour <sup>[2]</sup> | $10.8 | $10.8 | $10.8 |
| Total | | $11.9 | $21.8 | $120.8 |

1. Assumes that 10,000 messages are processed in roughly 1 min by Spark in Lambda.
2. One shard of provisioned Kinesis, more shards might be required for spiky workloads.

## Development

Use [pre-commit](https://pre-commit.com/).

```
pip install pre-commit
pre-commit
```

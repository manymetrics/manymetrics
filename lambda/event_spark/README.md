### Local setup

```
python -m venv env
source env/bin/activate
pip install pyspark==3.3.0 boto3

export SPARK_HOME=env/lib/python3.8/site-packages/pyspark
export ICEBERG_FRAMEWORK_VERSION=3.3_2.12
export ICEBERG_FRAMEWORK_SUB_VERSION=1.1.0
wget -q https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-${ICEBERG_FRAMEWORK_VERSION}/${ICEBERG_FRAMEWORK_SUB_VERSION}/iceberg-spark-runtime-${ICEBERG_FRAMEWORK_VERSION}-${ICEBERG_FRAMEWORK_SUB_VERSION}.jar -P ${SPARK_HOME}/jars/
wget -q https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.20.23/bundle-2.20.23.jar -P ${SPARK_HOME}/jars/
wget -q https://repo1.maven.org/maven2/software/amazon/awssdk/url-connection-client/2.20.23/url-connection-client-2.20.23.jar -P ${SPARK_HOME}/jars/
```

### Running locally

`export JAVA_HOME='/Library/Java/JavaVirtualMachines/jdk1.8.0_51.jdk/Contents/Home'`

`GLUE_DATABASE_NAME=manymetrics_lk1o4gzf EVENTS_S3_URI="s3://manymetrics-data-lk1o4gzf/data/events" spark-submit process_events.py --event "$(cat kinesis-event.json)"`

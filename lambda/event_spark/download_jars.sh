#!/usr/bin/env bash
SPARK_HOME=$1
AWS_SDK_VERSION=$2
ICEBERG_FRAMEWORK_VERSION=$3
ICEBERG_FRAMEWORK_SUB_VERSION=$4

mkdir $SPARK_HOME/conf
echo "SPARK_LOCAL_IP=127.0.0.1" > $SPARK_HOME/conf/spark-env.sh
echo "JAVA_HOME=/usr/lib/jvm/$(ls /usr/lib/jvm |grep java)/jre" >> $SPARK_HOME/conf/spark-env.sh

wget -q https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_VERSION}/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar -P ${SPARK_HOME}/jars/

echo "Downloading ICEBERG $ICEBERG_FRAMEWORK_VERSION-$ICEBERG_FRAMEWORK_SUB_VERSION"
wget -q https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-${ICEBERG_FRAMEWORK_VERSION}/${ICEBERG_FRAMEWORK_SUB_VERSION}/iceberg-spark-runtime-${ICEBERG_FRAMEWORK_VERSION}-${ICEBERG_FRAMEWORK_SUB_VERSION}.jar -P ${SPARK_HOME}/jars/
wget -q https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.20.23/bundle-2.20.23.jar -P ${SPARK_HOME}/jars/
wget -q https://repo1.maven.org/maven2/software/amazon/awssdk/url-connection-client/2.20.23/url-connection-client-2.20.23.jar -P ${SPARK_HOME}/jars/

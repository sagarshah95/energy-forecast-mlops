"""AWS Lambda S3 object metadata trigger; does not perform heavy ETL.

Week 6 scaffold: not deployed by infrastructure/terraform/main.tf.
Keep handlers short — S3 event payloads can fan out; heavy pandas belongs in a job.
"""
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(event, context):
    for record in event.get("Records", []):
        if record.get("eventSource") != "aws:s3":
            continue
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        logger.info("New object bucket=%s key=%s", bucket, key)
        # Next sprint: emit an EventBridge event / enqueue validated ingestion.
    return {"statusCode": 200, "body": json.dumps({"accepted": True})}

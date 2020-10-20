# twitter_to_redis
This application reads Tweets from Redis and stores the results in PostgreSQL.
It can be run wherever, but best works as a k8s Deployment.

## Environment variables
If you wish to use this application, you need to supply credentials for Redis and a PostgreSQL DB
This data is passed via environment variables.

## Logging
Logs are formatted for storage in Elasticsearch and sent to stdout.  
Since this app will run in k8s, k8s will automatically capture stdout at the node level.

## Monitoring
This application pushes custom metrics as a Prometheus exporter.
A Prometheus setup on a k8s node can scrape the metrics from container port 8080
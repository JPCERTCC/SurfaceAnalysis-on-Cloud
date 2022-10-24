import os
import json
import boto3
import hashlib
import datetime

JOB_QUEUE = os.environ['JOB_QUEUE']
JOB_DEFINITION = os.environ['JOB_DEFINITION']

HTML_REDIRECT = '''
<html>
<head>
  <meta charset="utf-8">
  <title>Analysis Results</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/css/bootstrap.min.css" integrity="sha384-+0n0xVW2eSR5OomGNYDnhzAbDsOXxcvSN1TPprVMTNDbiYZCxYbOOl7+AMvyTG2x" crossorigin="anonymous">
  <script>
    setTimeout("location.href='{redirect_url}'",6000*10);
  </script>
</head>
<body>
   <div class="container-fluid">
     <div class="row">
       <div class="col-sm-12 col-md-12 main mt-3">
         <p>60秒後にジャンプします。<br>
         ジャンプしない場合は、以下のURLをクリックしてください。</p>
         <p><a href="{redirect_url}">分析ページ</a></p>
      </div>
    </div>
  </div>
</body>
</html>
'''

def create_id(hashs):
    return hashlib.md5("".join(sorted(set(hashs))).encode("utf-8")).hexdigest()

def lambda_handler(event, context):
    hashs = json.loads(event['body'])
    id = create_id(hashs['hash'])
    print("[+] {0}: id {1}".format(datetime.datetime.now(), id))
    hashs['hash'].insert(0, "/tmp/run.sh")

    print("[+] {0}: commands {1}".format(datetime.datetime.now(), hashs['hash']))

    client = boto3.client('batch')

    response = client.submit_job(
        jobName = "AnalysisJob_" + id,
        jobQueue = JOB_QUEUE,
        jobDefinition = JOB_DEFINITION,
        containerOverrides={
            'command': hashs['hash']
            }
        )
    print(response)
    return {
        'statusCode':200,
        'headers':{
            'Content-Type': 'text/html',
        },
        #'body': HTML_REDIRECT.format(**{"redirect_url": "http://" + os.environ['S3_BUCKET'] + "/" + id + "/index.html"})
        'body': "http://" + os.environ['S3_BUCKET'] + "/" + id + "/index.html"
    }

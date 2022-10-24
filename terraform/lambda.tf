data "archive_file" "function_source" {
  type        = "zip"
  source_dir  = "Lambda"
  output_path = "archive/mal-analysis-func.zip"
}

resource "aws_lambda_function" "function" {
  function_name = local.function_name
  handler       = "lambda_function.lambda_handler"
  memory_size   = "128"
  role          = aws_iam_role.function_role.arn
  runtime       = "python3.8"
  timeout       = "10"

  filename         = data.archive_file.function_source.output_path
  source_code_hash = data.archive_file.function_source.output_base64sha256

  environment {
    variables = {
      JOB_QUEUE = aws_batch_job_queue.analysis.arn
      JOB_DEFINITION = "${var.app_name}_job"
      S3_BUCKET = aws_s3_bucket_website_configuration.analysis.website_endpoint
    }
  }

  tracing_config {
    mode = "PassThrough"
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_policy, aws_cloudwatch_log_group.lambda_log_group]
}

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name = "/aws/lambda/${local.function_name}"
}



# Crawler function for Lambda
resource "null_resource" "lambda_push" {
  provisioner "local-exec" {
    command = <<EOT
  pip install -r Lambda_crawler/requirements.txt -t Lambda_crawler/build/layer/python
  find Lambda_crawler/build -type f | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm
  curl -SL https://github.com/adieuadieu/serverless-chrome/releases/download/v1.0.0-37/stable-headless-chromium-amazonlinux-2017-03.zip > headless-chromium.zip
  curl -SL https://chromedriver.storage.googleapis.com/2.37/chromedriver_linux64.zip > chromedriver.zip
  unzip -o headless-chromium.zip -d Lambda_crawler/build/headless/python/bin
  unzip -o chromedriver.zip -d Lambda_crawler/build/headless/python/bin
      EOT
    interpreter = ["/bin/bash", "-c"]
    working_dir = path.module
  }
}

data "archive_file" "crawler_script" {
  type        = "zip"
  source_dir  = "Lambda_crawler/build/function"
  output_path = "archive/crawler-func.zip"

  depends_on = [null_resource.lambda_push]
}

data "archive_file" "layer_zip" {
  type        = "zip"
  source_dir  = "Lambda_crawler/build/layer"
  output_path = "archive/layer.zip"

  depends_on = [null_resource.lambda_push]
}

data "archive_file" "headless_zip" {
  type        = "zip"
  source_dir  = "Lambda_crawler/build/headless"
  output_path = "archive/headless.zip"

  depends_on = [null_resource.lambda_push]
}

resource "aws_lambda_layer_version" "lambda_layer" {
  layer_name = "${local.function_name_crawler}_layer"

  filename   = data.archive_file.layer_zip.output_path
  source_code_hash = data.archive_file.layer_zip.output_base64sha256
}

resource "aws_lambda_layer_version" "lambda_headless" {
  layer_name = "${local.function_name_crawler}_headless"

  filename   = data.archive_file.headless_zip.output_path
  source_code_hash = data.archive_file.headless_zip.output_base64sha256
}

resource "aws_lambda_function" "function_crawler" {
  function_name = local.function_name_crawler
  handler       = "lambda_function.lambda_handler"
  memory_size   = "1024"
  role          = aws_iam_role.function_role.arn
  runtime       = "python3.7"
  timeout       = "600"

  filename         = data.archive_file.crawler_script.output_path
  source_code_hash = data.archive_file.crawler_script.output_base64sha256

  layers = [aws_lambda_layer_version.lambda_layer.arn, aws_lambda_layer_version.lambda_headless.arn]

  environment {
    variables = {
      JOB_QUEUE = aws_batch_job_queue.analysis.arn
      JOB_DEFINITION = "${var.app_name}_job"
      S3_BUCKET = aws_s3_bucket_website_configuration.analysis.website_endpoint
      TWITTER_TOKEN = var.twitter_token
    }
  }

  tracing_config {
    mode = "PassThrough"
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_policy, aws_cloudwatch_log_group.lambda_log_group]
}

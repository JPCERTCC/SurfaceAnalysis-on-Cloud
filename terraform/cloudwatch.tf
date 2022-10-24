resource "aws_cloudwatch_event_rule" "every_day" {
  name                = "${local.name}_crawler"
  schedule_expression = "cron(0 0/6 * * ? *)"
}

resource "aws_cloudwatch_event_target" "every_day" {
  rule      = aws_cloudwatch_event_rule.every_day.name
  target_id = "function_crawler"
  arn       = aws_lambda_function.function_crawler.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_output_report" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.function_crawler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_day.arn

  depends_on    = [aws_lambda_function.function_crawler]
}


# Result submit event from S3
resource "aws_cloudwatch_event_rule" "batch-job" {
  name = "${local.name}-batch-job"

  event_pattern = <<EOF
  {
    "source": ["aws.batch"],
    "detail-type": ["Batch Job State Change"],
    "detail": {
      "status": ["FAILED", "SUCCESSED"],
      "jobQueue": ["${aws_batch_job_queue.analysis.arn}"]
    }
  }
EOF
}

resource "aws_cloudwatch_event_target" "sns" {
  rule = aws_cloudwatch_event_rule.batch-job.name
  arn  = aws_sns_topic.analysis.arn

  input_transformer {
    input_paths = {
      status   = "$.detail.status",
      jobName  = "$.detail.jobName",
    }
    input_template = "\"Malware analysis job <status> (Job name: <jobName>) \""
  }
}

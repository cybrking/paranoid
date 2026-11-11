resource "aws_s3_bucket" "invoices" {
  bucket = "orders-customer-invoices"
}

resource "aws_s3_bucket_public_access_block" "invoices" {
  bucket                  = aws_s3_bucket.invoices.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "invoices" {
  bucket = aws_s3_bucket.invoices.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.invoices.arn}/*"
    }]
  })
}

resource "aws_db_instance" "orders" {
  identifier             = "orders"
  engine                 = "postgres"
  instance_class         = "db.t4g.medium"
  allocated_storage      = 50
  username               = "orders"
  password               = var.db_password
  publicly_accessible    = true
  storage_encrypted      = false
  vpc_security_group_ids = [aws_security_group.db.id]
  skip_final_snapshot    = true
}

resource "aws_security_group" "db" {
  name = "orders-db"
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

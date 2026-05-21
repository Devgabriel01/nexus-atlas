# NEXUS ATLAS — AWS production stack
# Provisions: ECS Fargate (backend), CloudFront+S3 (frontend), RDS Postgres+PostGIS,
# Secrets Manager, ALB, ACM cert, Route53 record.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.50" }
  }
  backend "s3" {
    # configure on `terraform init -backend-config=`
    key = "nexus-atlas/terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" { default = "sa-east-1" }       # São Paulo
variable "project"    { default = "nexus-atlas" }
variable "domain"     { default = "nexus-atlas.com" }
variable "image_backend" { description = "Backend image (ghcr.io/.../backend:tag)" }
variable "groq_api_key"  { sensitive = true }
variable "gee_project"   { default = "" }

locals {
  tags = { Project = var.project, Environment = "prod" }
}

# ─── Networking ───────────────────────────────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.13"
  name    = "${var.project}-vpc"
  cidr    = "10.20.0.0/16"
  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  public_subnets  = ["10.20.1.0/24", "10.20.2.0/24"]
  private_subnets = ["10.20.10.0/24", "10.20.11.0/24"]
  enable_nat_gateway = true
  single_nat_gateway = true
  tags = local.tags
}

# ─── Database (RDS Postgres with PostGIS) ─────────────────────────────────
resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-db-subnets"
  subnet_ids = module.vpc.private_subnets
  tags       = local.tags
}

resource "aws_security_group" "db" {
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
  egress { from_port = 0 to_port = 0 protocol = "-1" cidr_blocks = ["0.0.0.0/0"] }
  tags = local.tags
}

resource "random_password" "db" {
  length  = 32
  special = true
}

resource "aws_db_instance" "postgres" {
  identifier              = "${var.project}-db"
  engine                  = "postgres"
  engine_version          = "16.3"
  instance_class          = "db.t4g.small"
  allocated_storage       = 50
  storage_type            = "gp3"
  storage_encrypted       = true
  db_name                 = "nexus_atlas"
  username                = "nexus"
  password                = random_password.db.result
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [aws_security_group.db.id]
  backup_retention_period = 14
  skip_final_snapshot     = false
  final_snapshot_identifier = "${var.project}-final-snapshot"
  publicly_accessible     = false
  tags = local.tags
}

# ─── Secrets ──────────────────────────────────────────────────────────────
resource "aws_secretsmanager_secret" "app" {
  name = "${var.project}/app"
  tags = local.tags
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    DATABASE_URL = "postgresql://nexus:${random_password.db.result}@${aws_db_instance.postgres.endpoint}/nexus_atlas"
    GROQ_API_KEY = var.groq_api_key
    GEE_PROJECT  = var.gee_project
    SECRET_KEY   = random_password.jwt.result
  })
}

resource "random_password" "jwt" {
  length  = 64
  special = false
}

# ─── Container compute (ECS Fargate) ──────────────────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "${var.project}-cluster"
  tags = local.tags
}

resource "aws_security_group" "app" {
  vpc_id = module.vpc.vpc_id
  ingress { from_port = 8000 to_port = 8000 protocol = "tcp" security_groups = [aws_security_group.alb.id] }
  egress { from_port = 0 to_port = 0 protocol = "-1" cidr_blocks = ["0.0.0.0/0"] }
  tags = local.tags
}

resource "aws_security_group" "alb" {
  vpc_id = module.vpc.vpc_id
  ingress { from_port = 443 to_port = 443 protocol = "tcp" cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 80  to_port = 80  protocol = "tcp" cidr_blocks = ["0.0.0.0/0"] }
  egress  { from_port = 0   to_port = 0   protocol = "-1"  cidr_blocks = ["0.0.0.0/0"] }
  tags = local.tags
}

resource "aws_lb" "main" {
  name               = "${var.project}-alb"
  load_balancer_type = "application"
  subnets            = module.vpc.public_subnets
  security_groups    = [aws_security_group.alb.id]
  tags               = local.tags
}

resource "aws_lb_target_group" "backend" {
  name        = "${var.project}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip"
  health_check { path = "/health" interval = 30 timeout = 5 healthy_threshold = 2 unhealthy_threshold = 3 }
}

# ACM certificate + HTTPS listener omitted for brevity — add aws_acm_certificate + Route53 validation.

resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project}-backend"
  cpu                      = "1024"
  memory                   = "2048"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_exec.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "backend"
    image     = var.image_backend
    essential = true
    portMappings = [{ containerPort = 8000, hostPort = 8000, protocol = "tcp" }]
    secrets = [
      { name = "DATABASE_URL", valueFrom = "${aws_secretsmanager_secret.app.arn}:DATABASE_URL::" },
      { name = "GROQ_API_KEY", valueFrom = "${aws_secretsmanager_secret.app.arn}:GROQ_API_KEY::" },
      { name = "GEE_PROJECT",  valueFrom = "${aws_secretsmanager_secret.app.arn}:GEE_PROJECT::" },
      { name = "SECRET_KEY",   valueFrom = "${aws_secretsmanager_secret.app.arn}:SECRET_KEY::" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.app.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "backend"
      }
    }
  }])
}

resource "aws_ecs_service" "backend" {
  name            = "${var.project}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  network_configuration {
    subnets         = module.vpc.private_subnets
    security_groups = [aws_security_group.app.id]
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }
  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project}"
  retention_in_days = 30
}

# IAM roles
resource "aws_iam_role" "ecs_exec" {
  name = "${var.project}-ecs-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_exec" {
  role       = aws_iam_role.ecs_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name = "${var.project}-ecs-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy" "ecs_task_secrets" {
  role = aws_iam_role.ecs_task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["secretsmanager:GetSecretValue"], Resource = [aws_secretsmanager_secret.app.arn] }]
  })
}

# ─── Frontend: S3 + CloudFront ────────────────────────────────────────────
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.project}-frontend-${var.aws_region}"
  tags   = local.tags
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  default_root_object = "index.html"
  aliases             = [var.domain]
  default_cache_behavior {
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    forwarded_values { query_string = false  cookies { forward = "none" } }
  }
  custom_error_response { error_code = 404 response_code = 200 response_page_path = "/index.html" }
  origin {
    domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id   = "s3-frontend"
    s3_origin_config { origin_access_identity = "" }
  }
  restrictions { geo_restriction { restriction_type = "none" } }
  viewer_certificate { cloudfront_default_certificate = true }
  tags = local.tags
}

output "alb_dns" { value = aws_lb.main.dns_name }
output "frontend_url" { value = "https://${aws_cloudfront_distribution.frontend.domain_name}" }
output "db_endpoint" { value = aws_db_instance.postgres.endpoint sensitive = true }

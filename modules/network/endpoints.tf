resource "aws_security_group" "endpoints" {
  count       = length(var.interface_endpoint_services) > 0 ? 1 : 0
  name        = "${var.env_name}-vpce-sg"
  description = "Allow HTTPS from within the VPC to interface endpoints"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = merge(local.tags, { Name = "${var.env_name}-vpce-sg" })
}

resource "aws_vpc_endpoint" "interface" {
  for_each            = toset(var.interface_endpoint_services)
  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${data.aws_region.current.region}.${each.value}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.endpoints[0].id]
  private_dns_enabled = true
  tags                = merge(local.tags, { Name = "${var.env_name}-vpce-${each.value}" })
}
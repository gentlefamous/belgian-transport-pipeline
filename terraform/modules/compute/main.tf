variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev or prod)"
  type        = string
}

# Databricks workspace
resource "azurerm_databricks_workspace" "main" {
  name                = "${var.project_name}-${var.environment}-dbw"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "trial"

  tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}
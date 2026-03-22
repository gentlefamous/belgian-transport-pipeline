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

# Storage Account with Data Lake Gen2 enabled
resource "azurerm_storage_account" "datalake" {
  name                     = replace("${var.project_name}${var.environment}dl", "-", "")
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true  # This enables Data Lake Gen2

  tags = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Raw data container — where Kafka lands Parquet files
resource "azurerm_storage_container" "raw" {
  name                  = "raw"
  storage_account_id    = azurerm_storage_account.datalake.id
  container_access_type = "private"
}

# Processed data container — where PySpark writes cleaned data
resource "azurerm_storage_container" "processed" {
  name                  = "processed"
  storage_account_id    = azurerm_storage_account.datalake.id
  container_access_type = "private"
}
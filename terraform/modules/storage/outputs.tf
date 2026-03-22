output "storage_account_name" {
  description = "Name of the Data Lake Storage account"
  value       = azurerm_storage_account.datalake.name
}

output "storage_account_id" {
  description = "ID of the Data Lake Storage account"
  value       = azurerm_storage_account.datalake.id
}
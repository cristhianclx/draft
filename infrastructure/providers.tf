terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3"
    }
    tidbcloud = {
      source  = "tidbcloud/tidbcloud"
      version = "~> 0.3"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

provider "tidbcloud" {
  sync = true
}

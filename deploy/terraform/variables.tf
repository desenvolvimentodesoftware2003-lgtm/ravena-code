# Variáveis para a Infraestrutura OCI da Ravena AI

variable "tenancy_ocid" {
  description = "OCID da Tenancy"
  type        = string
}

variable "user_ocid" {
  description = "OCID do Usuário"
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint da chave API"
  type        = string
}

variable "private_key_path" {
  description = "Caminho para a chave privada"
  type        = string
}

variable "region" {
  description = "Região da OCI"
  type        = string
  default     = "us-ashburn-1"
}

variable "compartment_id" {
  description = "OCID do Compartimento"
  type        = string
}

variable "availability_domain" {
  description = "Domínio de Disponibilidade"
  type        = string
}

variable "image_id" {
  description = "OCID da Imagem do SO (Ubuntu 22.04 recomendado)"
  type        = string
}

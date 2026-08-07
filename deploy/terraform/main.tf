# RAVENA AI v3.2.7 — OCI Infrastructure (Terraform)
# ================================================
# Este arquivo define a infraestrutura base na Oracle Cloud Infrastructure.

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# 1. Rede Virtual (VCN)
resource "oci_core_vcn" "ravena_vcn" {
  cidr_block     = "10.0.0.0/16"
  compartment_id = var.compartment_id
  display_name   = "Ravena_VCN_v3.2.7"
  dns_label      = "ravenavcn"
}

# 2. Sub-rede Privada (Para Agentes e Banco de Dados)
resource "oci_core_subnet" "ravena_private_subnet" {
  cidr_block        = "10.0.1.0/24"
  display_name      = "Ravena_Private_Subnet"
  compartment_id    = var.compartment_id
  vcn_id            = oci_core_vcn.ravena_vcn.id
  route_table_id    = oci_core_vcn.ravena_vcn.default_route_table_id
  security_list_ids = [oci_core_security_list.ravena_security_list.id]
  prohibit_public_ip_on_vnic = true
}

# 3. Security List (Protocolo R6 - Zero Trust)
resource "oci_core_security_list" "ravena_security_list" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.ravena_vcn.id
  display_name   = "Ravena_Security_List_R6"

  # Permitir tráfego interno apenas
  ingress_security_rules {
    protocol = "6" # TCP
    source   = "10.0.0.0/16"
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

# 4. Instância de Computação (OmegaCore)
resource "oci_core_instance" "ravena_omega_core" {
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_id
  display_name        = "Ravena_OmegaCore_v3.2.7"
  shape               = "VM.Standard.E4.Flex"

  shape_config {
    ocpus         = 2
    memory_in_gbs = 16
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.ravena_private_subnet.id
    display_name     = "PrimaryVNIC"
    assign_public_ip = false
  }

  source_details {
    source_type = "image"
    source_id   = var.image_id
  }
}

# 5. OCI Vault (Gerenciamento de Segredos - Lockdown V2.2)
resource "oci_kms_vault" "ravena_vault" {
  compartment_id = var.compartment_id
  display_name   = "Ravena_Vault_v3.2.7"
  vault_type     = "DEFAULT"
}

#!/usr/bin/env python
#
import logging
import adal
from azure.common.client_factory import get_client_from_cli_profile
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountCreateParameters
from azure.mgmt.storage.models import (StorageAccountCreateParameters,
                                       StorageAccountUpdateParameters,
                                       Sku,
                                       SkuName,
                                       Kind)

from azure.storage.blob import BlockBlobService
from msrestazure.azure_active_directory import AdalAuthentication
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD

# client = get_client_from_cli_profile(ComputeManagementClient)


LOG_FORMAT = "%(asctime)s %(levelname)s: [%(funcName)s] %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)


# paas_backrest.py sur directory group SA
# TENANT_ID = "15648b4a-b0fd-400e-b1d0-962d097b479a"
# CLIENT = "14e5f66e-e968-433c-a3bb-72b31b482893"

# test_bakrest sur directory jahia.com
# TENANT_ID = "7c97914f-5568-40eb-b95f-3b312c5a07a3"
# CLIENT = "31b6fbcb-ad93-4b1c-9d53-14748788191e"
# SECRET = "rrvO=v?gMGIIqiD7X/dv1Rf=ut2ueBv2"
#
# LOGIN_ENDPOINT = AZURE_PUBLIC_CLOUD.endpoints.active_directory
# RESOURCE = AZURE_PUBLIC_CLOUD.endpoints.active_directory_resource_id
#
# context = adal.AuthenticationContext(LOGIN_ENDPOINT + '/' + TENANT_ID)
# credentials = AdalAuthentication(
#     context.acquire_token_with_client_credentials,
#     RESOURCE,
#     CLIENT,
#     SECRET
# )

RG = "testlfu"
STO_ACCOUNT = "testlfu"

class PlayWithIt():
    def __init__(self, envname='testenv', accountID='testID',
                 region_name='us-central-1', env='prod',
                 accesskey=None, secretkey=None):
        self.envname = envname
        self.accountID = accountID
        self.region_name = region_name
        self.env = env
        self.accesskey = accesskey
        self.secretkey = secretkey
        self.tags = []

    def return_session(self, classname, method="client"):
        if method == "client":
            session = get_client_from_cli_profile(classname)
            return session

    def get_sto_account_key(self, rg=RG, sto_account=STO_ACCOUNT):
        client = self.return_session(StorageManagementClient)
        sto_keys = client.storage_accounts.list_keys(rg, sto_account)
        sto_keys = {v.key_name: v.value for v in sto_keys.keys}
        return sto_keys['key1']

    def check_if_sto_name_is_ok(self, sto_name):
        client = self.return_session(StorageManagementClient)
        response = client.storage_accounts.check_name_availability(sto_name)
        # print('The account {} is available: {}'
        #       .format(sto_name, availability.name_available))
        # print('Reason: {}'.format(availability.reason))
        # print('Detailed message: {}'.format(availability.message))
        if response.reason:
            logging.error(response.message)
            return response.name_available
        else:
            logging.info(response)
            return True

    def create_sto_container(self, sto_account, sto_cont_name,
                             rg=RG):
        key = self.get_sto_account_key(rg, sto_account)
        try:
            blob = BlockBlobService(sto_account, key)
        except:
            return False
        return blob.create_container(sto_cont_name)

    def delete_sto_container(self, sto_account, sto_cont_name,
                             rg=RG):
        key = self.get_sto_account_key(rg, sto_account)
        try:
            blob = BlockBlobService(sto_account, key)
        except:
            return False
        return blob.delete_container(sto_cont_name)

    def create_sto_account(self, sto_account, location, rg=RG):
        if not self.check_if_sto_name_is_ok(sto_account):
            return False
        client = self.return_session(StorageManagementClient)
        sto_async_operation = client.storage_accounts.create(
            rg, sto_account,
            StorageAccountCreateParameters(
                sku=Sku(name=SkuName.standard_ragrs),
                kind=Kind.storage_v2,
                location=location
            )
        )
        if sto_async_operation.result():
            logging.info("Storage {} is now created in {} on location {}"
                         .format(sto_account, rg, location))
            logging.debug(sto_async_operation.result())
            return True
        else:
            logging.error("Cannot create Storage Account {} in {}"
                          .format(sto_account, rg))
            logging.error(sto_async_operation.result())
            return False

    def delete_sto_account(self, sto_account, rg=RG):
        client = self.return_session(StorageManagementClient)
        try:
            sto_async_operation = client.storage_accounts.delete(
                rg, sto_account)
            logging.info("Storage {} is now deleted on {}"
                         .format(sto_account, rg))
        except:
            logging.error("Cannot delete Storage Account {} on {}")
            return False
        return True

    def test_if_obj_exist(self, sto_account, sto_cont_name, rg=RG,
                          object_name=None):
        sto_key = self.get_sto_account_key(rg, sto_account)
        blob = BlockBlobService(sto_account, sto_key)
        return blob.exists(sto_cont_name, object_name)


    def upload_file(self, file_name, sto_account, object_name=None,
                    rg=RG, sto_cont_name=None):

        if not self.test_if_obj_exist(sto_account, sto_cont_name, rg=RG):
            logging.info("{}:{}:{} does not exist, I will create it for you"
                         .format(rg, sto_account, sto_cont_name))
            self.create_sto_account(sto_account, self.region_name, rg=RG)
            self.create_sto_container(sto_account, sto_cont_name, rg=RG)

        # if blob object name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        sto_key = self.get_sto_account_key(rg, sto_account)
        blob = BlockBlobService(sto_account, sto_key)
        try:
            blob.create_blob_from_path(sto_cont_name, object_name,
                                       file_name)
            logging.info("File {} successfully uploaded to {}:{}:{}"
                         .format(file_name, sto_account,
                                 sto_cont_name, object_name))
        except:
            logging.error("Cannot upload {} to {}:{}:{}"
                          .format(file_name, sto_account,
                                  sto_cont_name, object_name))
            return False
        return True

    def delete_folder(self, sto_account, folder, rg=RG,
                      sto_cont_name=None):
        sto_key = self.get_sto_account_key(rg, sto_account)
        blob = BlockBlobService(sto_account, sto_key)
        folders = [b for b in blob.list_blobs(sto_cont_name)
                   if b.name.startswith(folder)]
        if len(folders) > 0:
            try:
                for f in folders:
                    blob.delete_blob(sto_cont_name, f.name)
                    logging.info("{}:{}:{} is now deleted"
                                .format(sto_account, sto_cont_name, f.name))
            except:
                logging.error("Error while deleting {}:{}:{}"
                              .format(sto_account, sto_cont_name, f.name))
                return False
        return True

    def folder_size(self, sto_account, folder, rg=RG,
                      sto_cont_name=None):
        sto_key = self.get_sto_account_key(rg, sto_account)
        blob = BlockBlobService(sto_account, sto_key)
        objects = [b for b in blob.list_blobs(sto_cont_name)
                   if b.name.startswith(folder + '/')]
        size = 0
        if len(objects) > 0:
            try:
                for f in objects:
                    size = size + f.properties.content_length
            except:
                logging.error("Something bad happened")
        return size

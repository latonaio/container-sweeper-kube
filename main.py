import os
from datetime import datetime
from itertools import groupby
from datetime import datetime
import threading
import time

import docker
from docker.errors import NotFound

from aion.logger import initialize_logger, lprint

SERVICE_NAME = "container-sweeper-kube"
CONTAINER_SIZE = 3
INTERVAL_TIME_SECOND = 3000 if os.environ.get("INTERVAL_TIME_SECOND") is None else int(os.environ.get("INTERVAL_TIME_SECOND"))

def parse_container_information(container):
    config = container.attrs['Config']
    return {
        'id': container.id,
        'name': container.name,
        'image': config['Image'],
        'command': config['Cmd'],
        'status': container.status,
        'created': container.attrs['Created']
    }

class DockerClient:
    def __init__(self):
        self.client = docker.from_env()

    def get_container_by_name(self, container_name):
        try:
            return self.client.containers.get(container_name)
        except NotFound:
            return None

    def stop_and_remove_container_by_name(self, container_name):
        container = self.get_container_by_name(container_name)
        if container is not None:
            container.stop()
            container.remove()
            lprint(f"success stop and remove container: {container_name}")
            return True
        else:
            lprint(f"cant stop and remove container: {container_name}")
            return False

    def remove_container(self, container):
        try:
            container_obj = self.get_container_by_name(container['name'])
            if container_obj:
                container_obj.remove()
                lprint(f"{container_obj} removed")
        except docker.errors.APIError as e:
            lprint(f" {container_obj} can't remove contaier for running")

    def get_container_information_by_name(self, container_name):
        container = self.get_container_by_name(container_name)
        return parse_container_information(container)

    def get_container_information_list(self):
        containers_list = []
        for new_container in self.client.containers.list(all=True):
            containers_list.append(parse_container_information(new_container))
        return containers_list

    def get_container_except_latest_n(self, contaierers_list, n):
        sorted_containers = sorted(contaierers_list,
                            key=(lambda con: con['created']), reverse=True)
        return sorted_containers[n:]

    def containers_groupby_service(self):
        _containers = self.get_container_information_list()
        # tagなしのサービス名を追加
        containers = map(lambda con:
                            {
                                'id': con['id'],
                                'name': con['name'],
                                'image': con['image'],
                                'created': con['created'],
                                'service' :con['image'].split(':')[0]
                            }, _containers)
        sort_containers = sorted(containers, key=(lambda con: con['service']))
        return groupby(sort_containers, key=(lambda con: con['service']))

class setInterval :
    def __init__(self,interval,action) :
        self.interval=interval
        self.action=action
        self.stopEvent=threading.Event()
        thread=threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self) :
        nextTime=time.time()+self.interval
        self.action()
        while not self.stopEvent.wait(nextTime-time.time()) :
            nextTime+=self.interval
            self.action()

def sweep_container():
    lprint(f"start on " + datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    # initialize docker client
    docker_client = DockerClient()
    containers = docker_client.get_container_information_list()
    for key, group in docker_client.containers_groupby_service():
        targets = docker_client.get_container_except_latest_n(list(group), CONTAINER_SIZE)
        if targets == []:
            lprint(f"there is no old container")
            continue
        for target in targets:
            docker_client.remove_container(target)

def main():
    initialize_logger(SERVICE_NAME)
    setInterval(INTERVAL_TIME_SECOND, sweep_container)

if __name__ == "__main__":
    main()


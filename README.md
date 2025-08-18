# npp
(a nicotine++ (a nicotine+ (a graphical client for the Soulseek peer-to-peer network) fork) fork)

Nicotine++ is a vitaminized version of the popular [Soulseek](https://www.slsknet.org/) client [Nicotine+](https://nicotine-plus.org/), designed to run headlessly in a docker container and expose an API s.t. any client may search/download using the Soulseek P2P network. This project aims to expand the API for the purpose of being used in `recotine`, an in-development automated music discovery tool for Navidrome and similar Subsonic-API reliant music servers.


## Prerequisites

- Docker v20 or higher.
- Docker compose v2.

## Install

The installation steps are:

1. Checkout the repository in your machine.
2. The next step is optional. If you want to define your own folder structure where the files are downloaded you have to edit the `docker-compose.yaml` file. You only have to change the path that is before the colon `:`.
    ```
    volumes:
      - ./npp_data/transfers/downloads:/data/nicotine/downloads
      - ./npp_data/transfers/incomplete:/data/nicotine/incomplete
      - ./npp_data/transfers/received:/data/nicotine/received
      - ./npp_data/config:/config/nicotine
    
    ```
3. Open a command prompt, navigate to the repository root folder and run the following command:  
   - Windows: ```docker compose up -d --build```
   - Raspberry Pi: ```docker-compose up -d --build``` (make sure that the package ```docker-compose``` is installed in your Raspi)

And that's it! Nicotine++ should be now running on your machine. 

When you create the docker container for the first time, by default, Nicotine++ will generate random user and password so that you can connect to the network. In case you want to use your own credentials you can stop the container and change them in the config file. Once you save the changes on the configuration file, the container will read and use the new credentials.

## API

```
Documentation under construction
```

## Nicotine+
In case you want further information about Nicotine+ and its source code, please check the original repository [here](https://github.com/nicotine-plus/nicotine-plus).

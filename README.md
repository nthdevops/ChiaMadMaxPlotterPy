# Gerenciador Plotter MadMax
#
#
## Descrição do Projeto
##### O script irá criar plots NFT baseada na configuração indicada para múltiplos diretórios, removendo a necessidade de criação manual de plots para vários diretórios
#
#
### Pré-requisitos

##### Antes de começar, você vai precisar renomear o arquivo conf.json.example para conf.json e realizar a configuração:
#
#
##### O arquivo .example estará no seguinte formato:
#
```javascript
{
    "threads": (-1 para todas as threads do sistema ou o valor que desejar, Exemplo: 4),
    "tempDir": "TempDir terminado com\\",
    "farmerKey": "Farmer Public Key",
    "madMaxOptionalArgs": {
        "buckets": "default", (Ira definir o numero de buckets utilizados para criacao de plots, deixe o parametro como "default" para nao alterar o valor padrao que o madMax usa, para utilizar, insira o numero de buckets sem aspas, exemplo: 512)
        "buckets3": "default", (Ira definir o numero de buckets utilizados para criacao de plots na fase 3 e 4, deixe o parametro como "default" para nao alterar o valor padrao que o madMax usa, para utilizar, insira o numero de buckets sem aspas, exemplo: 512)
        "waitForCopy": "default", (Utilizado para esperar para a copia de um plot antes de iniciar um novo, caso queira alterar para esperar, mude de "default" para "yes" para habilitar)
        "rMulti2": "default" (Multiplicador de threads para a fase 2, deixe como "default" para nao alterar ou coloque o numero que deseja multiplicar sem aspas para utilizar, exemplo: 2)
    },
    "finalDirs": [
        {
            "path": "Diretorio Final terminado com\\",
            "maxPlots": "Numero maximo de plots para este diretorio final. ESCREVER O NUMERO SEM AS ASPAS" Exemplo: 5,
            "nftAddress": "Chave NFT da pool"
        }
    ],
    "logsPath": "Diretorio para os logs do MadMax",
    "loglevel": "info" OU "debug",
    "deleteTempBeforeStart": true/false, ira deletar arquivos .plot.temp que podem ter ficado de resquicios de outra plotagem nao finalizada
}
```

##### Exemplo de arquivo de configuração final com diretórios de rede e locais configurados:
#
```javascript
{
    "threads": -1,
    "tempDir": "C:\\Users\\USER\\Chia\\TempPlots\\",
    "farmerKey": "farmerKey",
    "madMaxOptionalArgs": {
        "buckets": "default",
        "buckets3": "default",
        "waitforcopy": "default",
        "rmulti2": "default"
    },
    "finalDirs": [
        {
            "path": "C:\\Users\\USER\\Chia\\ChiaNFTPlots\\",
            "maxPlots": 10,
            "nftAddress": "xchSINGLETON"
        },
        {
            "path": "\\\\DESKTOP-NETWORKNAME\\Folder\\ChiaNFTPlots\\",
            "maxPlots": 15,
            "nftAddress": "xchSINGLETON"
        }
    ],
    "logsPath": "C:\\Users\\USER\\Chia\\logs\\",
    "loglevel": "info",
    "deleteTempBeforeStart": true
}
```

##### Adicione quantos elementos forem necessários em finalDirs!
#
##### Agora basta iniciar o executável "startPlots.exe".
#
#
### Veja também:
- [Script de substituição de plots antigos](https://github.com/nthdevops/oldPlotsReplacer)
#
##### Donate XCH: xch1dp7urpgy6uafhxnt305pj8hq2nqkdasycgrmnmwwtnc2542lnrvsdanazj
#
### Faça download:
- [Releases](https://github.com/nthdevops/ChiaMadMaxPlotterPy/releases)
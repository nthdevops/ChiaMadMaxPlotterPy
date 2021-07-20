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
    "finalDirs": [
        {
            "path": "Diretorio Final terminado com\\",
            "maxPlots": "Numero maximo de plots para este diretorio final. ESCREVER O NUMERO SEM AS ASPAS" Exemplo: 5,
            "nftAddress": "Chave NFT da pool"
        }
    ],
    "farmerKey": "Farmer Public Key",
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
    "farmerKey": "farmerKey",
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
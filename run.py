import psutil, os, atexit, shutil, subprocess, requests, time, jsonConf, sys, logging
from sys import exit
from datetime import datetime

# Retorna o path do arquivo de acordo com o tipo de execucao, se for binario ou o script diretamente
def filePath():
    path = ""
    if getattr(sys, 'frozen', False):
            path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(os.path.abspath(__file__))
    return path

#Define o diretorio atual do arquivo em execucao
thisFilePath = str(filePath())

#Vai para o diretorio atual do arquivo
os.chdir(thisFilePath)

#Cria o objeto de configuracao do atraves da classe de json
conf = jsonConf.getConf(thisFilePath+'\\conf.json')

#Logging config
loglevel = getattr(logging, conf.loglevel.upper())
logging.basicConfig(handlers=[logging.FileHandler(filename=conf.logsPath+'plotter.log', 
                                                 encoding='utf-8-sig', mode='w')], format='%(message)s', level=loglevel)
def strListFromArgs(args):
    compiledStr = str(args[0])
    sizeArgs = len(args)
    if sizeArgs > 1:
        for x in range(1, sizeArgs):
            compiledStr += " " + str(args[x])
    return compiledStr

def debug(*args):
    messageList = strListFromArgs(args)
    logging.debug(messageList)

def info(*args):
    messageList = strListFromArgs(args)
    logging.info(messageList)
    print(messageList)

def warning(*args):
    messageList = strListFromArgs(args)
    logging.warning(messageList)
    print(messageList)

def error(*args):
    messageList = strListFromArgs(args)
    logging.error(messageList)
    print(messageList)

#Declaracao de variaveis globais
endString = "\nPrograma finalizado!\nBye Bye :)\n"

#Plotting control
psPlotsCreating = []
plotsLogsHistory = {}

#API Conf
plotReplaceAPIUrl = "http://"+conf.plotReplaceAPI.host+":"+conf.plotReplaceAPI.port+"/addPlotToDelete"

#Funcao para remover os diretorios temporarios
def removeTempDirs():
    try:
        tempDirs = os.listdir(conf.tempDir)
        if len(tempDirs) > 0:
            info("\nDeletando diretorios temporarios")
            for dir in tempDirs:
                dirDel = conf.tempDir+dir
                info("\nDeletando diretorio:", dirDel)
                cntTries = 0
                while True:
                    if os.path.exists(dirDel):
                        cntTries += 1
                        removeDir(dirDel)
                    else:
                        info("Diretorio deletado!")
                        break
                    if cntTries >= 20:
                        warning("Nao conseguiu deletar o diretorio!")
                        break
                    time.sleep(1)
    except Exception as e:
        error("\nNao conseguiu deletar os diretorios temporarios, Excecao:\n"+ str(e))

#Funcao para finalizar o plotter
def finishMadMaxPlotter():
    info("\n\nFinalizando execucao do programa, aguarde!")
    psPlotCreatingRemoveAll()
    info("\nQuase finalizando..")
    removeTempDirs()
    
    info(endString)
    input("Pressione 'Enter' para sair...")

#Funcoes em caso de abortar o programa
atexit.register(finishMadMaxPlotter)

#Valida se os diretorios estao corretos, caso algum esteja errado finaliza a execucao
for dir in conf.finalDirs:
    confPath = dir["path"]
    if(os.path.exists(confPath)):
        continue
    else:
        error("\nNao foi possivel encontrar o diretorio " + confPath + ", configurado como path!")
        exit()

#Funcao de limpeza de diretorios
def cleanDir(path):
    dir = os.listdir(path)
    for file in dir:
        os.remove(path+"\\"+file)

#Funcao de acoes para usar tempdir
def createTempDir(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            cleanDir(path)
    except Exception as e:
        error("\n\nNao foi possivel criar pastas temporarias!\nExcecao:", e)
        exit()

#Funcao de remocao de diretorios
def removeDir(path):
    shutil.rmtree(path, ignore_errors=True)

#Le o log retornando as linhas tratadas
def readLog(logPath):
    if os.path.isfile(logPath):
        with open(logPath, encoding='utf-8-sig') as f:
            lines = f.read().splitlines()
        return lines
    else:
        error("Arquivo de log", logPath, "nao foi encontrado!")
        return [""]

#Valida se existe um texto em uma linha, para inumeros parametros
def checktextInStr(line, *args):
    if args[0] in line:
        if len(args) == 1:
            return True
        foundAll = True
        for arg in args:
            if arg not in line:
                foundAll = False
                break
        if foundAll:
            return True
    return False

#Funcao para iniciar a plotagem
def startMadMaxPlotter(plots, finalDir, contractAdress):
    #Cria o plot name para tempDirs e logs a partir do horario de criacao
    now = datetime.now()
    plotName = "plot_"+now.strftime("%d_%m_%Y__%H-%M-%S")
    logName = conf.logsPath+plotName+".log"
    tempDir1 = conf.tempDir+plotName+"Temp1\\"
    tempDir2 = conf.tempDir+plotName+"Temp2\\"
    createTempDir(tempDir1)
    createTempDir(tempDir2)
    #Define a quantidade de threads a serem utilizadas
    totalThreads = int(conf.threads)
    if(totalThreads < 0):
        totalThreads = psutil.cpu_count()

    commandString = 'powershell \".\chia_plot.exe -n \'' + str(plots) +'\' -r \'' + str(totalThreads) + '\' -t \'' + tempDir1 + '\' -2 \'' + tempDir2 + '\' -d \'' + str(finalDir) + '\' -c \'' + str(contractAdress) + '\' -f \'' + conf.farmerKey + '\' | Out-File \'' + logName + '\' -Encoding UTF8\"'

    psProcess = None
    try:
        psProcess = subprocess.Popen(commandString)
    except KeyboardInterrupt:
        warning("\nExecucao interrompida!")
    except Exception as e:
        error("\nNao conseguiu plotar!\n",e)
        exit()
    #Retorna um dict com as informacoes de criacao de plot do madMax
    return {"psProcess": psProcess, "logName": logName, "created": False}

#Conta o total de plots no diretorio
def getPlotsCount(plotsPath):
    totalPlots = len([f for f in os.listdir(plotsPath) if len(f.split('.plot')) == 2])
    return totalPlots

# A partir de um diretorio do arquivo de configuracao, cria um dict de facil acesso com as informacoes daquele diretorio
def getPlotDirInfos(dir):
    finalPath = dir["path"]
    maxPlots = int(dir["maxPlots"])
    nftAddress = dir["nftAddress"]
    replaceOldPlotsEnabled = dir["replaceOldPlots"]["enabled"]
    replaceOldPlotsDeletePath = dir["replaceOldPlots"]["deletePath"]
    jsonDeletePath = {"deletePath": replaceOldPlotsDeletePath}
    totalPlotsNft = getPlotsCount(finalPath)
    
    dirInfos = {}
    dirInfos["finalPath"] = finalPath
    dirInfos["maxPlots"] = maxPlots
    dirInfos["nftAddress"] = nftAddress
    dirInfos["replaceOldPlotsEnabled"] = replaceOldPlotsEnabled
    dirInfos["replaceOldPlotsDeletePath"] = replaceOldPlotsDeletePath
    dirInfos["jsonDeletePath"] = jsonDeletePath
    dirInfos["totalPlotsNft"] = totalPlotsNft
    return dirInfos

# Printa as informacoes a partir de um dict de dir retornado pela funcao getPlotDirInfos
def printPlotDirInfos(dirInfos):
    info("Path final:", dirInfos["finalPath"])
    info("Max Plots:", dirInfos["maxPlots"])
    info("NFT Singleton:", dirInfos["nftAddress"])
    info("Substituir plots antigos:", dirInfos["replaceOldPlotsEnabled"])
    info("Diretorio plots antigos:", dirInfos["replaceOldPlotsDeletePath"])

# Requisita para a API de substituicao de plots a partir das infos de diretorio da funcao getPlotDirInfos
def requestReplaceAPI(dirInfos):
    requestSent = False
    if dirInfos["replaceOldPlotsEnabled"]:
        if conf.plotReplaceAPI.ignoreFirst:
            conf.plotReplaceAPI.ignoreFirst = False
            return False

        info("\nEnviando requisicao para replace de plot..")
        while not requestSent:
            try:
                r = requests.post(plotReplaceAPIUrl, json=dirInfos["jsonDeletePath"], timeout=120)
            except Exception as e:
                error("\nNao foi possivel requisitar para a API, verifique possiveis problemas. Excecao:\n", e)
            else:
                requestSent = True
    return requestSent

# Retorna a valicao de criacao de plot para o diretorio
def canCreatePlot(dirInfos):
    return dirInfos["totalPlotsNft"] < dirInfos["maxPlots"]

# A partir de um elemento da lista psPlotsCreating, inicia a criacao do plot
def plotCreate(psPlotElem):
    psPlotDirInfo = psPlotElem["dirInfo"]
    #Prints iniciais
    info("\n=========================================================================================================")
    info("Iniciando criacao de plot!\n")
    printPlotDirInfos(psPlotDirInfo)
    #Inicia o madMaxPlotter, armazenando o retorno da funcao
    madProcess = startMadMaxPlotter(1, psPlotDirInfo["finalPath"], psPlotDirInfo["nftAddress"])
    #Adiciona a lista de processos do elemento de criacao de plots
    psPlotElem["madMaxProcess"].append(madProcess)
    #Incrementa o valor de plots NFT do diretorio
    psPlotElem["dirInfo"]["totalPlotsNft"] += 1
    newLogName = madProcess["logName"]
    info("\nIniciou a criacao do plot", psPlotElem["dirInfo"]["totalPlotsNft"], "de", psPlotElem["dirInfo"]["maxPlots"], "| Arquivo de log:", newLogName)
    cntTries = 0
    #Validacao para o output do madMax, somente dando continuidade quando o arquivo de log for criado, provando que o MadMax iniciou, desiste apos 50 tentativas
    while not os.path.isfile(newLogName):
        cntTries += 1
        if cntTries == 50:
            error("Arquivo de log nao foi encontrado | log:", newLogName)
            break
        time.sleep(0.5)
    newLogLines = None
    cntTries = 0
    mustBreak = False
    #Enquanto nao sair o output com o nome do plot, sai da iteracao para a mensagem de criacao ficar completa, desistindo apos 50 tentativas
    while not mustBreak:
        time.sleep(0.5)
        cntTries += 1
        newLogLines = readLog(newLogName)
        for line in newLogLines:
            if checktextInStr(line, "Plot Name: "):
                info(line)
                mustBreak = True
                break
        if cntTries == 50:
            break
    plotsLogsHistory[madProcess["logName"]] = newLogLines
    info("=========================================================================================================\n\nPlot em criacao...")

#Valida qual diretorio ira iniciar a nova criacao de plot e inicia
def newPlot():
    #Variavel para dizer se conseguiu ou nao criar plots, indicando que acabou a criacao de plots se o valor for False no retorno
    plotCreated = False
    for psPlotElem in psPlotsCreating:
        if canCreatePlot(psPlotElem["dirInfo"]):            
            plotCreate(psPlotElem)
            plotCreated = True
            break
    return plotCreated

# Remove da lista de plots em criacao, o elemento indicado
def psPlotCreatingRemove(psMadMaxProcess, madProcess):
    try:
        madProcess["psProcess"].terminate()
    except:
        pass
    plotsLogsHistory.pop(madProcess["logName"], None)
    psMadMaxProcess.remove(madProcess)

# Remove todos os elementos da lista de plots em criacao
def psPlotCreatingRemoveAll():
    for psPlot in psPlotsCreating:
        for madProcess in psPlot["madMaxProcess"]:
            psPlotCreatingRemove(psPlot["madMaxProcess"], madProcess)

debug("Ira iniciar agora!\nConfiguracao definida:\n", conf.values())

try:
    # Deleta diretorios temporarios, antes de iniciar a execucao
    removeTempDirs()

    #Cria a fila de criacao de plots
    for dir in conf.finalDirs:
        dirInfo = getPlotDirInfos(dir)
        #Antes de fazer o append para a lista psPlotsCreating, valida se ainda ha espaco para criacao de plots
        if canCreatePlot(dirInfo):
            psPlotsCreating.append({"dirInfo": dirInfo, "madMaxProcess": []})
        else:
            info("\n=========================================================================================================")
            info("\nNao sera necessaria a criacao de plots para o dir:")
            printPlotDirInfos(dirInfo)
            info("\nO numero maximo de plots ja foi atingido!")
            info("\n=========================================================================================================")

    #Inicia a criacao do primeiro plot, se nao criar, finaliza o programa, ja que todos os diretorios estao cheios e nao sera necessario criar plots
    if not newPlot():
        exit()

    while(True):
        #Itera sobre a lista de criacao de plots
        for psPlot in psPlotsCreating:
            #Valida se para o elemento da lista, existem plots em criacao atraves da lista que controla processo do madMax
            if len(psPlot["madMaxProcess"]) > 0:
                dirInfo = psPlot["dirInfo"]
                #Itera sobre todos os processos em andamento na lista
                for madProcess in psPlot["madMaxProcess"]:
                    log = madProcess["logName"]
                    logLines = readLog(log)
                    if logLines != None:
                        #So entra nas validacoes se o log foi alterado, caso esteja igual ao historico, nao realiza nenhuma acao
                        if logLines != plotsLogsHistory[log]:
                            for line in logLines:
                                #Somente valida linhas novas do arquivo de log, evitando reprocessamento desnecessario
                                if line not in plotsLogsHistory[log]:
                                    debug("\nNova linha detectada no log:", line)
                                    #Print caso o log seja sobre a finalizacao de uma das fases do MadMax
                                    if checktextInStr(line, "Phase ", " took "):
                                        info("\n" + line)
                                    #Valida atraves do atributo de criacao de log se o log ainda esta sendo criado
                                    elif not madProcess["created"]:
                                        #Checka atraves da mensagem se o log foi criado, caso sim, print da finalizacao, deleta um plot antigo e inicia outra criacao de plot
                                        if checktextInStr(line, "Total plot creation time"):
                                            info("\n" + line,"| log:", log)
                                            madProcess["created"] = True
                                            if requestReplaceAPI(dirInfo):
                                                info("\nResposta com sucesso para replace de plots antigos!")
                                            newPlot()
                                            break
                                    #Caso seja um plot ja criado, valida se a copia do arquivo foi terminada, caso sim, elimina o elemento da lista de processos do madMax
                                    elif checktextInStr(line, "Started copy to "):
                                        info("\n" + line,"| log:", log)
                                    elif checktextInStr(line, "Copy to", "finished, took"):
                                        info("\n" + line,"| log:", log)
                                        psPlotCreatingRemove(psPlot["madMaxProcess"], madProcess)
                                        break
                            #Adiciona as novas linhas de log ao historico, apos o processamento finalizar
                            plotsLogsHistory[log] = logLines
            #Se o primeiro if, disser que a lista de processos do madMax esta vazia, ira validar para que remova da lista de criacao de plots caso nao seja possivel criar novos plots para o diretorio em questao
            elif not canCreatePlot(psPlot["dirInfo"]):
                info("\n=========================================================================================================")
                info("\nCriacao de plots finalizada para:")
                printPlotDirInfos(dirInfo)
                psPlotsCreating.remove(psPlot)
                info("\n=========================================================================================================")
        
        #Caso nao exista elementos para criacao de plots, finaliza o loop, partindo para o fim do programa
        if len(psPlotsCreating) == 0:
            info("\n---------------------------------------------------------------------------------------------------------")
            info("\nCriacao de plots finalizada para todos os diretorios!\n\nO programa ira finalizar em breve!")
            info("\n---------------------------------------------------------------------------------------------------------")
            break
        time.sleep(5)
except KeyboardInterrupt:
    warning("\nExecucao interrompida!")

# Caso tudo tenha corrido bem, finaliza o programa
exit()
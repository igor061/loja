# encoding: utf-8
from HTMLParser import HTMLParser
from collections import deque, namedtuple


class ParseNFeHtml(HTMLParser):
    '''Converte um buffer contendo um html do site da receita em um map no padrao da classe NFe2
    '''

    def __init__(self):
        HTMLParser.__init__(self)
        self.fifo = deque()
        self.mapNfe = dict()
        self.mapNFeValidado = dict()

    def doParser(self, buf):
        self.fifo = deque()
        # Faz o parser do html e insere na fila os dados
        self.feed(buf)
        #printFIFO(self.fifo)
        # Trata os dados e gera um Map com as chaves a partir do html
        mapHtml = self._geraMap()
        #printAll(mapHtml)

        # gera um map no padrao da classe NFe2
        self.mapNFeValidado = self._nfeHtml2nfe(mapHtml)
        return self.mapNFeValidado


    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            d = dict(attrs)
            clas = d.get('class')
            if clas:
                if clas == 'TituloAreaRestritacentro':
                    self.fifo.append(('ST-TD-CLASS-TARC', ))
                elif clas == 'TituloAreaRestrita2':
                    self.fifo.append(('ST-TD-CLASS-TAR2', ))
                    #print "achou ",clas
                elif clas == 'TituloAreaRestrita':
                    self.fifo.append(('ST-TD-CLASS-TAR', ))

        elif tag == 'span':
            clas = dict(attrs).get('class', '')

            if clas == 'TextoFundoBrancoNegrito':
                self.fifo.append(('ST-SPAN-CLASS-TFBN', ))
            elif clas == 'linha':
                self.fifo.append(('ST-SPAN-CLASS-LINHA', ))


    def handle_data(self, data):
        data = data.lstrip().rstrip().replace('\n', '').replace('\r', '')

        self.fifo.append(('DATA', data))




    def _geraMap(self):

        resp = dict()
        self.listaProds = []
        resp['produtos'] = self.listaProds

        prox = self._carregaDict(resp, ('novo', 'inicial'))

        while prox and prox[0] == 'produto':
            prox = self._carregaDict(self.listaProds, prox)

        prox = self._carregaDict(resp, prox)

        return resp


    def _carregaDict(self, dictPai, prox):

        #print "#carregadict: ", prox[1]

        while prox and prox[0] != None:
            dictAtual = dict()
            if isinstance(dictPai, dict):
                dictPai[prox[1]] = dictAtual
            else:
                dictPai.append(dictAtual)

            atual = prox
            prox = self._carregaDadosDict(dictAtual, atual[1])

            #print "atual: %s | prox: %s" % (atual.__str__(), prox.__str__())

            if atual[0] == 'subgrupo':
                return prox

            while prox and prox[0] == 'subgrupo':
                prox = self._carregaDict(dictAtual, prox)
            if atual[0] == 'produto':
                return prox
            if prox[0] == 'produto':
                return prox

    def _carregaDadosDict(self, dictAtual, dictNome):

        chaves = deque()

        while self.fifo:
            next = self.fifo.popleft()


            if next[0] == 'ST-SPAN-CLASS-TFBN':
                #achou uma CHAVE
                chave = self._pegaDado()
                if chave:
                    if chave == "Num.": # é um produto
                        self.fifo.appendleft(('DATA', 'ID'))
                        self.fifo.appendleft(('ST-SPAN-CLASS-TFBN', ))
                        return (('produto', 'produto'))
                    else:
                        chaves.append(chave) # coloca em uma fila, pois os itens que estao na mesma linha
                                         # ficam agrupados e depois a medida que aparecem os valores elas sao consumidas
                else:
                    # ignorando
                    #dictAtual['@#%04d' % len(dictAtual)] = 'ST-SPAN-CLASS-TFBN - Sem dados'
                    pass
            elif next[0] == 'ST-SPAN-CLASS-LINHA':
                # achou um VALOR para chave
                valor = self._pegaDado()
                if chaves:
                    dictAtual[chaves.popleft()] = valor
                else:
                    #achou um valor sem chave
                    dictAtual['anon%04d' % len(dictAtual)] = valor

            elif next[0] == 'ST-TD-CLASS-TARC':
                # Começou um novo Grupo
                proxNome = self._pegaDado()
                if proxNome:
                    return ('novo', proxNome)
                else:
                    # nao é para acontecer
                    dictAtual['@#%04d' % len(dictAtual)] = 'ST-TD-CLASS-TARC - Sem nome'

            elif (next[0] == 'ST-TD-CLASS-TAR') or (next[0]=='ST-TD-CLASS-TAR2'):
                # Pode ter achado um novo sub-grupo
                subgrupoNome = self._pegaDado()
                if(subgrupoNome != None):
                    # Achou um novo sub-grupo, se nao ignora a tupla
                    return ('subgrupo', subgrupoNome)
            elif (next[0] == 'DATA'):
                # descarta tuplas DATA sem chave
                #print "## Descartando:", next
                pass
            else: # Nao soube tratar a tupla
                dictAtual['@#%04d' % len(dictAtual)] = next

        return (None, )


    def _pegaDado(self):
        #print '#pegadata'
        resp = None
        while self.fifo:
            next = self.fifo.popleft()
            if next[0] == 'DATA':
                if next[1] != '':
                    resp = next[1]
                    break
            else:
                self.fifo.appendleft(next)
                break

        #print '#Pegou data: ', resp
        return resp

    def _nfeHtml2nfe(self, mapHtml):


        mapResp = dict()

        mapRespValores = dict()
        mapResp['valores'] = mapRespValores

        mapRespDadosNfe = dict()
        mapResp['dadosNfe'] = mapRespDadosNfe

        mapRespEmitente = dict()
        mapResp['emitente'] = mapRespEmitente

        mapRespDestinatario = dict()
        mapResp['destinatario'] = mapRespDestinatario

        mapICMS = mapHtml['Totais']['ICMS']
        mapRespValores['frete'] = convertStrToFloat(mapICMS['Valor do Frete'])
        mapRespValores['descontos'] = convertStrToFloat(mapICMS['Valor Total dos Descontos'])
        mapRespValores['seguro'] = convertStrToFloat(mapICMS['Valor do Seguro'])
        mapRespValores['produtos'] = convertStrToFloat(mapICMS['Valor Total dos Produtos'])

        mapInicial = mapHtml['inicial']
        mapRespDadosNfe['chaveDeAcesso'] = mapInicial['Chave de Acesso']

        mapDadosNfe = mapHtml['Dados da NF-e']
        mapRespDadosNfe['dataEmissao'] = mapDadosNfe['Data de emiss\xe3o']
        mapRespDadosNfe['numero'] = mapDadosNfe['N\xfamero']
        mapRespDadosNfe['serie'] = mapDadosNfe['S\xe9rie']
        mapRespValores['total'] = convertStrToFloat(mapDadosNfe['Valor Total da Nota Fiscal'])

        chaveSituacaoAtual = filter(lambda x: x.startswith('SITUA\xc7\xc3O ATUAL'), mapDadosNfe.keys())[0]
        mapRespDadosNfe['situacao'] = mapDadosNfe[chaveSituacaoAtual]['Ocorr\xeancia']

        mapDadosDestinatario = mapDadosNfe['DESTINAT\xc1RIO']
        mapRespDestinatario['CNPJ'] = mapDadosDestinatario['CNPJ'].replace('.', '').replace('/', '').replace('-', '')
        mapRespDestinatario['razaoSocial'] = mapDadosDestinatario['Nome/Raz\xe3o Social']

        mapDadosEmitente = mapDadosNfe['EMITENTE']
        mapRespEmitente['CNPJ'] = mapDadosEmitente['CNPJ'].replace('.', '').replace('/', '').replace('-', '')
        mapRespEmitente['razaoSocial'] = mapDadosEmitente['Nome/Raz\xe3o Social']


        mapResp['duplicatas'] = self._geraDuplicatas(mapHtml)
        mapResp['produtos'] = self._geraProdutos(mapHtml)

        return mapResp

    def _geraDuplicatas(self, mapNfe):

        duplicatas = []
        cobranca = mapNfe.get('Dados de Cobran\xe7a')
        if cobranca:
            mapDadosDuplicatas = cobranca['DUPLICATAS']

            if mapDadosDuplicatas:
                dd = deque([ v for k, v in sorted(mapDadosDuplicatas.items())])
                duplicatas.append((
                    dd[0],
                    dd[2],
                    convertStrToFloat(dd[1])
                    ))

                x = 3
                while x < len(dd):
                    duplicatas.append((
                        dd[x],
                        dd[x+1],
                        convertStrToFloat(dd[x+2]),
                        ))
                    x += 3

        return tuple(duplicatas)

    def _geraProdutos(self, mapNfe):
        produtos = []
        listaProdutos = mapNfe['produtos']

        for prod in listaProdutos:
            pd = dict()
            produtos.append(pd)

            pd['id'] = prod['ID']
            pd['codigo'] = prod['C\xf3digo do Produto']
            pd['descricao'] = prod['Descri\xe7\xe3o']
            pd['qtd'] = convertStrToFloat(prod['Qtd.'])
            pd['desconto'] = convertStrToFloat(prod.get('Valor do Desconto'))
            pd['frete'] = convertStrToFloat(prod.get('Valor do Frete'))
            pd['valor'] = convertStrToFloat(prod['Valor(R$)'])
            pd['valorUnitario'] = convertStrToFloat(prod['Valor unit\xe1rio de comercializa\xe7\xe3o'])
            pd['seguro'] = convertStrToFloat(prod.get('Valor do Seguro'))
            pd['codigoEAN'] = prod['C\xf3digo EAN Comercial']

            mapIPI = prod.get('IMPOSTO SOBRE PRODUTOS INDUSTRIALIZADOS')
            if mapIPI:
                ipi = convertStrToFloat(mapIPI.get('Valor IPI'))

            pd['ipi'] = ipi



        return tuple(produtos)


class NFe2:

    def __init__(self, mapNfe):
        self.destinatario = CadastroNFe2(mapNfe['destinatario'])
        self.emitente = CadastroNFe2(mapNfe['emitente'])
        self.duplicatas = DuplicatasNFe2(mapNfe['duplicatas'])
        self.produtos = ProdutosNFe2(mapNfe['produtos'])

        mapDadosNfe = mapNfe['dadosNfe']
        self.chaveDeAcesso = mapDadosNfe['chaveDeAcesso']
        self.dataEmissao = mapDadosNfe['dataEmissao']
        self.numero = mapDadosNfe['numero']
        self.serie = mapDadosNfe['serie']
        self.situacao = mapDadosNfe['situacao']
        self.valores = ValoresNFe2(mapNfe['valores'])

        if abs(self.valores.total - self.produtos.valorTotalCusto()) > 0.02:
            printAll(self)
            raise NFe2Exception("Valor da Nota [%.2f] difere do somatorio de custo dos produtos [%.2f]" %
                                (self.valores.total, self.produtos.valorTotalCusto()))


class NFe2Exception(Exception):
    pass


class ValoresNFe2:
    def __init__(self, map):
        self.total = map['total']
        self.desconto = map['descontos']
        self.frete = map['frete']
        self.produtos = map['produtos']
        self.seguro = map['seguro']


class CadastroNFe2:
    def __init__(self, map):
        self.CNPJ = map['CNPJ']
        self.razaoSocial = map['razaoSocial']

class DuplicatasNFe2:
    def __init__(self, listDuplicatas):
        self.duplicatas = listDuplicatas

class ProdutosNFe2:
    def __init__(self, listaProd):
        self.lista = []
        for x in listaProd:
            self.lista.append(ProdutoNFe2(x))

    def qtdPecas(self):
        return reduce(lambda x,y: x+y, [k.qtd for k in self.lista])

    def valorTotal(self):
        return reduce(lambda x,y: x+y, [k.valor for k in self.lista])

    def valorTotalFrete(self):
        return reduce(lambda x,y: x+y, [k.frete for k in self.lista])

    def valorTotalSeguro(self):
        return reduce(lambda x,y: x+y, [k.seguro for k in self.lista])

    def qtdItens(self):
        return len(lista)

    def valorTotalCusto(self):
        return reduce(lambda x,y: x+y, [k.custo() for k in self.lista])


class ProdutoNFe2:
    def __init__(self, map):
        self.codigoEAN = map['codigoEAN']
        self.qtd = map['qtd']

        self.frete = map['frete']
        self.valor = map['valor']
        self.seguro = map['seguro']
        self.desconto = map['desconto']
        self.valorUnitario = map['valorUnitario']
        self.ipi = map['ipi']

        self.codigo = map['codigo']
        self.id = map['id']
        self.descricao = map['descricao']


    def custo(self):
        return self.valor + self.frete + self.seguro + self.ipi - self.desconto



def printFIFO(fifo,sep = ''):
    for x in fifo:
        print sep, 'id'
        printAll(x, sep)


def printDict(data, sep = ''):
    for x in sorted(data.items()):
        printAll(x[1], sep, x[0])

def printInstance(data, sep = ''):
    printAll(vars(data), sep)


def printAll(data, sep='', pref=''):
    sep += '    '
    if isinstance(data, deque):
        printFIFO(data, sep)
    elif isinstance(data, list):
        print sep, pref
        printFIFO(data, sep)
    elif isinstance(data, dict):
        print sep, pref
        printDict(data,sep)
    elif str(type(data)) ==  "<type 'instance'>":
        print sep, pref
        printInstance(data, sep)
    else:
        print sep, pref, ':', data

def convertStrToFloat(str):
    if str:
        return float(str.replace('.', '').replace(',', '.'))
    else:
        return 0.0
def convertStrToInt(str):
    if str:
        return int(str.replace('.', ''))
    else:
        return 0

def printPrecoVenda(nfe2, markup):
    print
    print "Loja:", nfe2.destinatario.razaoSocial
    print "Fornecedor:", nfe2.emitente.razaoSocial
    print "Série / Número da Nota:", nfe2.serie, " /", nfe2.numero
    print
    print "frete: %.2f%%" % (100.0*nfe2.valores.frete/(nfe2.valores.produtos - nfe2.valores.desconto))
    print "desconto: %.2f%%" % (100.0*nfe2.valores.desconto/nfe2.valores.produtos)
    print "seguro: %.2f%%" % (100.0*nfe2.valores.seguro/(nfe2.valores.produtos - nfe2.valores.desconto))
    print
    for prod in sorted(nfe2.produtos.lista, key=lambda p: p.codigo):
        print "%6.2f - %2d - %s - %s" % (prod.custo()*markup/prod.qtd, prod.qtd, prod.codigo, prod.descricao)

if __name__ == "__main__":
    #f = open('../../download/NFe Orient 136704.html')
    #f = open('../../download/NFe Technos 249946.html')
    #f = open('../../download/NFe Orient 136703.html')
    #f = open('../../download/NFe Seculus 190377.html')
    #f = open('../../download/NFe Seculus 191501.html')
    #f = open('../../download/NFe CPL 3100.html')
    f = open('Armani 22559.html')
    buf = f.read()

    parser = ParseNFeHtml()
    mapNfe2 = parser.doParser(buf)
    #printAll(parser.mapNfe)

    nfe2 = NFe2(mapNfe2)

    #print printAll(vars(nfe2))

    printPrecoVenda(nfe2, 2.5)

    #print nfe2.produtos.valorTotalCusto()



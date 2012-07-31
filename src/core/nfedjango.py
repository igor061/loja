# encoding: utf-8

import django_tables2 as dtables


class NFe2ProdutoTable(dtables.Table):
        id = dtables.Column(verbose_name='id')
        qtd = dtables.Column(verbose_name='qtd')
        preco = dtables.Column(verbose_name='Preco Venda')
        codigo = dtables.Column(verbose_name='Codigo')
        descricao = dtables.Column(verbose_name='Descricao')
        valorUnitario = dtables.Column()
        desconto = dtables.Column()
        frete = dtables.Column()
        ipi = dtables.Column()
        valor = dtables.Column()
        seguro = dtables.Column()
        custo = dtables.Column()
        codigoEAN = dtables.Column()

        class Meta:
            pass
            orderable = False
            order_by = 'codigo'
            exclude = ("valorUnitario", "desconto", "frete", "ipi", "valor", "seguro", "custo", "codigoEAN")


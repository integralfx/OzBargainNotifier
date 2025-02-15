from OzBargain import OzBargain

if __name__ == '__main__':
    ozb = OzBargain()

    # db_sales = [x for x in ozb.load_sales() if not ozb.has_expired(x)]
    # ozb_sales = [x for x in ozb.get_ebay_sales() if not ozb.has_expired(x)]
    # new_sales = [x for x in ozb_sales if not ozb.sale_exists(x['id'], db_sales)]
    # longest = len(max(new_sales, key=lambda x: len(x['title']))['title'])
    # for sale in new_sales:
    #     print(f'{sale["title"].ljust(longest)} | {sale["link"].replace("goto", "node")}')

    # ozb.save_sales(new_sales)

    # sales = ozb.get_ebay_sales()
    # for sale in sales:
    #     print(sale['title'])
    #     for cat in sale['categories']:
    #         print(f'\t{cat["name"]} | {cat["link"]}')
    # ozb.save_sales(sales)

    for sale in ozb.load_sales():
        print(f'{sale["title"]} | {sale["link"]}')
        for cat in sale['categories']:
            print(f'\t{cat["name"]} | {cat["link"]}')
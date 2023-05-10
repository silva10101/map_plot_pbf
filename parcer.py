OSM_FILE = "/home/bulat/Downloads/mz.osm.pbf"
import osmium
import os
import sqlite3



class CounterHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)

        print('initializing db')
        # open the file
        file_name = f'{OSM_FILE.split("/")[-1][:-8]}.db'
        if os.path.exists(file_name):
            os.remove(file_name)
        # connecting for the database
        self.con = sqlite3.connect(file_name)
        self.cur = self.con.cursor()
        print('initialized db')
        # создание таблиц нод
        self.cur.execute("""CREATE TABLE IF NOT EXISTS nodes(
            id INTEGER PRIMARY KEY NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL)""")     
        print('created table nodes')
        # создание таблиц структур
        self.cur.execute("""CREATE TABLE IF NOT EXISTS ways(
                id INTEGER PRIMARY KEY NOT NULL,
                tag TEXT NOT NULL,
                loc TEXT NOT NULL)""")
        print('created table ways')

    def node(self, n):
        '''inserting nodes'''
        # creating list of nodes names 
        name = str(n).split(':')[0][1:]
        # inserting in table
        self.cur.execute('''INSERT INTO nodes (id, lat, lon)
                            VALUES (?, ?, ?)''', (name, 
                                      n.location.lat, 
                                      n.location.lon))

    def way(self, w):
        '''inserting ways'''
        tag_list = list()
        loc_list = list()
        # creating list with tags
        for tag in w.tags:
            tag_list.append(str(tag))
        # creating list with locations of nodes
        for n in w.nodes:
            self.cur.execute(f'''SELECT lat,lon FROM nodes 
                                    WHERE id = {n}''')
            query = self.cur.fetchone()
            loc_list.append(str([query[0], query[1]]))
        # inserting in table
        self.cur.execute('''INSERT INTO ways (id, tag, loc)
                            VALUES (?, ?, ?)''', (w.id, 
                                    ';'.join(tag_list), 
                                    ';'.join(loc_list)))

    def relation(self, r):
        pass

    def commit_base(self):
        """apply changes and close bd"""
        self.con.commit()
        self.con.close()
               

if __name__ == '__main__':
    counter = CounterHandler()
    if not os.path.exists(OSM_FILE):
        raise FileNotFoundError(f"File {OSM_FILE} not found.")
    else:
        counter.apply_file(OSM_FILE)
        counter.commit_base()

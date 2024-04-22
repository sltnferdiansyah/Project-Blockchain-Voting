import hashlib
import json
from database import konekdb

mydb, cur = konekdb() # buat koneksi ke database

# buat tabel blockchain 
cur.execute("""
CREATE TABLE IF NOT EXISTS blocks (
            vote_id INT AUTO_INCREMENT PRIMARY KEY,
            vote_index INT,
            timestamp DATETIME,
            data TEXT,
            previous_hash VARCHAR(64),
            hash VARCHAR(64)
)
""")

class Block:
    def __init__(self, vote_index, timestamp, data, previous_hash):
        self.vote_index = vote_index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            'vote_index': self.vote_index,
            'timestamp': str(self.timestamp),
            'data': self.data,
            'previous_hash': self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def to_dict(self):
        return {
            'vote_index': self.vote_index,
            'timestamp': str(self.timestamp),
            'data': self.data,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }
    
class Blockchain:
    def __init__(self):
        self.chain = self.load_blocks_from_database()

    def load_blocks_from_database(self):
        cur.execute("SELECT * FROM blocks ORDER BY vote_id ASC")
        blocks = []
        for row in cur.fetchall():
            block_data = json.loads(row[3])
            block = (row[1],row[2],block_data,row[4])
            block.hash = row[5]
            blocks.append(block)
        return blocks
    
    def validate_block(self, new_block):
        previous_block_index = len(self.chain) - 1 # mengambil data terakhir dari self.chain
        earliest_deleted_index = None # menyimpan index yang tidak valid
        found_block_valid = False

        while previous_block_index >= 0: # melakukan looping validasi hash dari block sebelumnya
            previous_block = self.chain[previous_block_index] # mendapatkan index terakhir
            calculated_hash = previous_block.calculate_hash() # melakukan hashing pada index terakhir

            if calculated_hash == previous_block.hash:
                new_block.previous_hash = previous_block.hash 
                found_block_valid = True
                break # jika block sebelumnya valid maka looping berhenti
            else: # jika tidak valid maka akan menghapus index yang tidak valid dan melakukan hash pada block sebelumnya lagi
                self.remove_block(previous_block_index)
                if earliest_deleted_index is None or previous_block_index < earliest_deleted_index:
                    earliest_deleted_index = previous_block_index
                previous_block_index -= 1 # mengurangi index

        if found_block_valid: # jika ditemukan block yang valid maka akan menambahkan block baru
            if earliest_deleted_index is not None:
                new_block.vote_index = earliest_deleted_index
            self.add_block(new_block)
            print("Voting berhasil ditambahkan")
            return True
        else:
            print("Tidak ada data yang valid")
            return False
        
    def remove_block(self, vote_index):
        block_to_remove = self.chain[vote_index]

        cur.execute("DELETE FROM blocks WHERE vote_index = %s", (block_to_remove.vote_index,))
        mydb.commit()
        del self.chain[vote_index]

    def add_block(self, new_block):
        cur.execute("""
        INSERT INTO blocks (vote_index, timestamp, data, previous_hash,hash) VALUES (%s,%s,%s,%s,%s)
        """, (new_block.vote_index, new_block.timestamp, json.dumps(new_block.data), new_block.previous_hash, new_block.hash))
        mydb.commit()
        self.chain.append(new.block)







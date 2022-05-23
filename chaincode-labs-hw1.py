#!/usr/bin/env python3	

'''
Look at example_test.py in the functional test directory and try getting node 1 to mine another block, send it to node 2, and check that node 2 received it. In your response to this email, please include a link to a gist or code snippet that you used to complete this step.
'''

from collections import defaultdict
from test_framework.blocktools import (create_block, create_coinbase)
from test_framework.messages import CInv, MSG_BLOCK
from test_framework.p2p import (
    P2PInterface,
    msg_block,
    msg_getdata,
    p2p_lock,
)
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import (
    assert_equal,
)

class BaseNode(P2PInterface):
    def __init__(self):
        super().__init__()
        # Stores a dictionary of all blocks received
        self.block_receive_map = defaultdict(int)

        def on_block(self, message):
        	"""Store the hash of a received block in the dictionary."""
	        message.block.calc_sha256()
	        self.block_receive_map[message.block.sha256] += 1

        def on_inv(self, message):
        	"""Override the standard on_inv callback"""
        	pass

class WasBlockReceived(BitcoinTestFramework):

    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 3
        self.extra_args = [[], ["-logips"], []]

    def setup_network(self):
        self.setup_nodes()
        self.connect_nodes(0, 1)
        self.sync_all(self.nodes[0:2])

    def run_test(self):
        """Main test logic"""

        peer_messaging = self.nodes[0].add_p2p_connection(BaseNode())

        blocks = [int(self.generate(self.nodes[0], sync_fun=lambda: self.sync_all(self.nodes[0:2]), nblocks=1)[0], 16)]

        self.log.info("Mine block with node 1")
        self.tip = int(self.nodes[1].getbestblockhash(), 16)
        self.block_time = self.nodes[1].getblock(self.nodes[1].getbestblockhash())['time'] + 1
        height = self.nodes[1].getblockcount()
        block = create_block(self.tip, create_coinbase(height+1), self.block_time)
        block.solve()
        block_message = msg_block(block)
        peer_messaging.send_message(block_message)
        self.tip = block.sha256
        blocks.append(self.tip)

        self.log.info("Connect node 1 and node 2 and propagates mined block")
        self.connect_nodes(1, 2)
        self.sync_all()
        self.nodes[1].disconnect_p2ps()

        self.log.info("Check if node 2 received it")
        assert_equal(self.nodes[1].getbestblockhash(), self.nodes[2].getbestblockhash())

if __name__ == '__main__':
    WasBlockReceived().main()

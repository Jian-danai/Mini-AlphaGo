# -*- coding: utf-8 -*-
from math import *
import random

class OthelloState:
    def __init__(self,sz = 8):
        self.playerJustMoved = 2 # player-1 has the first move
        self.board = [] # 0 = empty, 1 = player 1, 2 = player 2
        self.size = sz
        assert sz == int(sz) and sz % 2 == 0 # size must be integral and even
        for y in range(sz):
            self.board.append([0]*sz)
        self.board[int(sz/2)][int(sz/2)] = 1
        self.board[int(sz/2-1)][int(sz/2-1)] = 1
        self.board[int(sz/2)][int(sz/2-1)] = 2
        self.board[int(sz/2-1)][int(sz/2)] = 2

    def Clone(self):
        """ Create a deep clone of this game state.
        """
        st = OthelloState()
        st.playerJustMoved = self.playerJustMoved
        st.board = [self.board[i][:] for i in range(self.size)]
        st.size = self.size
        return st

    def DoMove(self, move):
        """ Update a state by carrying out the given move.
            Must update playerToMove.
        """
        (x,y)=(move[0],move[1])
        assert x == int(x) and y == int(y) and self.IsOnBoard(x,y) and self.board[x][y] == 0
        m = self.GetAllSandwichedCounters(x,y)
        self.playerJustMoved = 3 - self.playerJustMoved
        self.board[x][y] = self.playerJustMoved
        for (a,b) in m:
            self.board[a][b] = self.playerJustMoved
    
    def GetMoves(self):
        """ Get all possible moves from this state.
        """
        return [(x,y) for x in range(self.size) for y in range(self.size) if self.board[x][y] == 0 and self.ExistsSandwichedCounter(x,y)]

    def AdjacentToEnemy(self,x,y):
        """ Speeds up GetMoves by only considering squares which are adjacent to an enemy-occupied square.
        """
        for (dx,dy) in [(0,+1),(+1,+1),(+1,0),(+1,-1),(0,-1),(-1,-1),(-1,0),(-1,+1)]:
            if self.IsOnBoard(x+dx,y+dy) and self.board[x+dx][y+dy] == self.playerJustMoved:
                return True
        return False
    
    def AdjacentEnemyDirections(self,x,y):
        """ Speeds up GetMoves by only considering squares which are adjacent to an enemy-occupied square.
        """
        es = []
        for (dx,dy) in [(0,+1),(+1,+1),(+1,0),(+1,-1),(0,-1),(-1,-1),(-1,0),(-1,+1)]:
            if self.IsOnBoard(x+dx,y+dy) and self.board[x+dx][y+dy] == self.playerJustMoved:
                es.append((dx,dy))
        return es
    
    def ExistsSandwichedCounter(self,x,y):
        """ Does there exist at least one counter which would be flipped if my counter was placed at (x,y)?
        """
        for (dx,dy) in self.AdjacentEnemyDirections(x,y):
            if len(self.SandwichedCounters(x,y,dx,dy)) > 0:
                return True
        return False
    
    def GetAllSandwichedCounters(self, x, y):
        """ Is (x,y) a possible move (i.e. opponent counters are sandwiched between (x,y) and my counter in some direction)?
        """
        sandwiched = []
        for (dx,dy) in self.AdjacentEnemyDirections(x,y):
            sandwiched.extend(self.SandwichedCounters(x,y,dx,dy))
        return sandwiched

    def SandwichedCounters(self, x, y, dx, dy):
        """ Return the coordinates of all opponent counters sandwiched between (x,y) and my counter.
        """
        x += dx
        y += dy
        sandwiched = []
        while self.IsOnBoard(x,y) and self.board[x][y] == self.playerJustMoved:
            sandwiched.append((x,y))
            x += dx
            y += dy
        if self.IsOnBoard(x,y) and self.board[x][y] == 3 - self.playerJustMoved:
            return sandwiched
        else:
            return [] # nothing sandwiched

    def IsOnBoard(self, x, y):
        return x >= 0 and x < self.size and y >= 0 and y < self.size
    
    def GetResult(self, playerjm):
        """ Get the game result from the viewpoint of playerjm. 
        """
        jmcount = len([(x,y) for x in range(self.size) for y in range(self.size) if self.board[x][y] == playerjm])
        notjmcount = len([(x,y) for x in range(self.size) for y in range(self.size) if self.board[x][y] == 3 - playerjm])
        if jmcount > notjmcount: return 1.0
        elif notjmcount > jmcount: return 0.0
        else: return 0.5 # draw

    def __repr__(self):
        s= ""
        for y in range(self.size-1,-1,-1):
            for x in range(self.size):
                s += ".XO"[self.board[x][y]]
            s += "\n"
        return s

class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    def __init__(self, move = None, parent = None, state = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.untriedMoves = state.GetMoves() # future child nodes
        self.playerJustMoved = state.playerJustMoved # the only part of the state that the Node needs later
        
    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
        return s
    
    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes.append(n)
        return n
    
    def Update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        return "[M:" + str((self.move[0],7-self.move[1]))+str(self.move) + " Q=W/V:" + str(self.wins) + "/" + str(self.visits) +"="+str(self.wins/self.visits) +" U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
             s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
             s += str(c) + "\n"
        return s

half_corner=[(0,1),(1,0),(0,6),(1,7),(6,0),(7,1),(7,6),(6,7)]
pre_corner=[(1,1),(6,6),(1,6),(6,1)]
def UCT(rootstate, itermax, verbose = False):
    """ Conduct a UCT search for itermax iterations starting from rootstate.
        Return the best move from the rootstate.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""
    try:
        corner_index=[x in rootstate.GetMoves() for x in [(0,0),(7,0),(0,7),(7,7)]].index(True)
        print('太爽了')
        return [(0,0),(7,0),(0,7),(7,7)][corner_index]
    except:
        pass

    rootnode = Node(state = rootstate)

    for i in range(itermax):
        ## 该itermax实际控制了搜索树的size

        ## 每一次循环都将rootstate复制进行操作
        ## 但是最后的update会更新rootstate的值

        ## state是复制的变量
        ## 但是node仅仅是rootnode的引用

        node = rootnode
        state = rootstate.Clone()


        ## 遍历已经查找过并且有子节点的节点
        while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
            node = node.UCTSelectChild()
            state.DoMove(node.move)

        ## 现在node(即rootnode)在有未尝试的叶节点的节点上

        # Expand
        if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
            m = random.choice(node.untriedMoves) 
            state.DoMove(m)
            node = node.AddChild(m,state) # add child and descend tree

            ## 现在node是本轮扩展的子节点，state是node根据执行m扩展的子节点的state
            ## 该子节点 state=state parent=之前的node
        # 第三个
        else:
            ## 此时认为搜索树已经完全扩展了
            break

        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        ## 从子节点的state出发，随机抽取move进行模拟

        ## 第二个改进
        if str(state).count('.')>=-1:
            while state.GetMoves() != []:  # while state is non-terminal
                state.DoMove(random.choice(state.GetMoves()))
        else:
            ## use min_max
            print('min max')
            pass

        # Backpropagate

        # tmp_result=
        while node != None: # backpropagate from the expanded node and work back to the root node

            ## 第一个改进：加入规则判断，提高边角权重，降低半角权重
            # if node.move in []:
            #     # state is terminal. Update node with result from POV of node.playerJustMoved
            #     _weight=0.2
            #     node.Update(state.GetResult(node.playerJustMoved)+_weight)
            # else:
                # state is terminal. Update node with result from POV of node.playerJustMoved
            node.Update(state.GetResult(node.playerJustMoved))
            node = node.parentNode

    # Output some information about the tree - can be omitted
    if (verbose): print (rootnode.TreeToString(0))
    else: print (rootnode.ChildrenToString())

    for childNode in rootnode.childNodes:
        if childNode.move in half_corner:
            print(childNode.visits,end='\t')
            x=0 if childNode.move[0] < 4 else 7
            y=0 if childNode.move[0] < 4 else 7
            # chess = 'O' if rootstate.playerJustMoved ==
            if rootstate.board[x][y] != 2:
                childNode.visits *= 0.1

            print(childNode.move,'太菜了',childNode.visits)
        elif childNode.move in pre_corner:
            print(childNode.visits,end='\t')
            x=0 if childNode.move[0] < 4 else 7
            y=0 if childNode.move[0] < 4 else 7
            # chess = 'O' if rootstate.playerJustMoved ==
            if rootstate.board[x][y] != 2:
                childNode.visits *= 0.4

            print(childNode.move,'半菜了',childNode.visits)
        else:
            x=childNode.move[0]
            y=childNode.move[1]
            if x in [0,7] or y in [0,7]:
                childNode.visits *= 1.5
                print(childNode.move,'优先占边')
    return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited
                
def UCTPlayGame():
    """ Play a sample game between two UCT players where each player gets a different number 
        of UCT iterations (= simulations = tree nodes).
    """
    state = OthelloState()
    while (state.GetMoves() != []):
        print (str(state))
        if state.playerJustMoved == 1:
            m = UCT(rootstate = state, itermax = 1000, verbose = False) # play with values for itermax and verbose = True
            print ("Player",state.playerJustMoved,"Best Move: " + str((m[0],7-m[1])) + "\n")

        else:
            m = UCT(rootstate = state, itermax = 1000, verbose = False)
            print ("Player",state.playerJustMoved,"Best Move: " + str((m[0],7-m[1])) + " with minmax\n")
        state.DoMove(m)
    if state.GetResult(state.playerJustMoved) == 1.0:
        print ("Player " + str(state.playerJustMoved) + " wins!")
    elif state.GetResult(state.playerJustMoved) == 0.0:
        print ("Player " + str(3 - state.playerJustMoved) + " wins!")
    else: print ("Nobody wins!")


## 执行gui传回的move
def UCTreceive(state,x,y):
    print(x,y)
    state.DoMove((x,y))
    return state

## 根据GUI传回的state计算ai的move
def UCTaimove(state):

    ## ai先走一步
    state.DoMove(UCT(rootstate = state, itermax = 10, verbose = False))
    ## 每次ai走完棋之后 player会反转

    ## 人没有棋可走 令ai连续走棋
    while state.GetMoves()==[]:
        state.playerJustMoved=3-state.playerJustMoved
        ## ai 没有棋可走
        if state.GetMoves()==[]:
            ## 游戏结束
            return state.GetResult(playerjm=state.playerJustMoved)

        ## ai 尚有棋可走
        else:
            ## 每次ai走完棋之后 player会反转
            state.DoMove(UCT(rootstate=state, itermax=10, verbose=False))
    return state

if __name__ == "__main__":
    """ Play a single game to the end using UCT for both players. 
    """
    UCTPlayGame()
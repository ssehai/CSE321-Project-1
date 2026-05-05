import math

# B-tree

class BTreeNode:
    def __init__(self, is_leaf=False):
        self.keys = []        # sorted list of keys
        self.rids = []        # rids[i] corresponds to keys[i]
        self.children = []    # len(children) == len(keys) + 1 for internal nodes
        self.is_leaf = is_leaf


class BTree:
    def __init__(self, n):
        self.n = n
        self.root = BTreeNode(is_leaf=True)
        self.split_count = 0
        self.total_nodes = 1
        self.total_keys = 0

    def _find_path(self, key):
        """Return the path from the root to correct place"""
        path = []
        node = self.root
        path.append([node, -1])
        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1
            node = node.children[i]
            path.append([node, i])
        return path
        

    def search(self, key):
        """Return RID if found, else None."""
        node = self.root
        while True:
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1
            if i < len(node.keys) and key == node.keys[i]:  # find correct node
                return node.rids[i]
            if node.is_leaf:    # key is not found
                return None
            node = node.children[i]

    def insert(self, key, rid):
        """Insert (key, rid) into the appropriate leaf. Split as needed."""
        path = self._find_path(key)
        cur_node = path[-1][0]
        idx = 0
        while idx < len(cur_node.keys) and key > cur_node.keys[idx]:
            idx += 1
        cur_node.keys.insert(idx, key)
        cur_node.rids.insert(idx, rid)
        self.total_keys += 1
        
        # Split occur!
        if len(cur_node.keys) == self.n:
            self.split_count += 1
            i = math.ceil(self.n/2)
            sep_key = cur_node.keys[i-1]
            sep_rid = cur_node.rids[i-1]
            new_node = BTreeNode(is_leaf=True)
            self.total_nodes += 1
            new_node.keys = cur_node.keys[i:]
            new_node.rids = cur_node.rids[i:]
            del cur_node.keys[i-1:], cur_node.rids[i-1:]

            # Only root
            if len(path) == 1:
                new_root = BTreeNode()
                self.total_nodes += 1
                new_root.keys = [sep_key]
                new_root.rids = [sep_rid]
                new_root.children = [cur_node, new_node]
                self.root = new_root
                return 

            # Insert seperator key and new_node into the internal node's keys and children
            idx = 0
            j = -2
            while idx < len(path[j][0].keys) and sep_key > path[j][0].keys[idx]:
                idx += 1
            path[j][0].keys.insert(idx, sep_key)
            path[j][0].rids.insert(idx, sep_rid)
            path[j][0].children.insert(idx + 1, new_node)
            # Check splits in internal nodes
            while len(path[j][0].keys) == self.n:
                self.split_count += 1
                sep_key = path[j][0].keys[i-1]
                sep_rid = path[j][0].rids[i-1]
                new_node = BTreeNode()
                self.total_nodes += 1
                new_node.keys = path[j][0].keys[i:]
                new_node.rids = path[j][0].rids[i:]
                new_node.children = path[j][0].children[i:] # i가 맞나?
                del path[j][0].keys[i-1:], path[j][0].rids[i-1:], path[j][0].children[i:]

                if path[j][1] == -1:    # reached to the root
                    new_root = BTreeNode()
                    self.total_nodes += 1
                    new_root.keys = [sep_key]
                    new_root.rids = [sep_rid]
                    new_root.children = [self.root, new_node]
                    self.root = new_root
                    return 
                j -= 1
                idx = 0
                while idx < len(path[j][0].keys) and sep_key > path[j][0].keys[idx]:
                    idx += 1
                path[j][0].keys.insert(idx, sep_key)
                path[j][0].rids.insert(idx, sep_rid)
                path[j][0].children.insert(idx + 1, new_node)

    def delete(self, key):
        """Delete key from tree. Handle underflow via merge or redistribution."""
        if self.search(key) is None:    return
        path = []
        node = self.root
        path.append([node, -1])

        match_node = None
        match_idx = None

        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1
            if i < len(node.keys) and node.keys[i] == key:
                match_node = node
                match_idx = i
                break
            node = node.children[i]
            path.append([node, i])
        
        if match_node is None and node.is_leaf:
            if key in node.keys:
                match_node = node
                match_idx = node.keys.index(key)

        if match_node.is_leaf: # just delete it
            del_node = match_node
            del_idx = match_idx
        else:
            # find successor and swap it
            node = match_node.children[match_idx + 1]
            path.append([node, match_idx + 1])
            while not node.is_leaf:
                node = node.children[0]
                path.append([node, 0])
            successor = node
            # swap with successor
            match_node.keys[match_idx] = successor.keys[0]
            match_node.rids[match_idx] = successor.rids[0]
            del_node = successor
            del_idx = 0
        # delete key and rid in the leaf node
        del del_node.keys[del_idx], del_node.rids[del_idx]

        self.total_keys -= 1
        if len(path) == 1:  # Only root
            return
        # Handle underflow
        min_keys = math.ceil(self.n / 2) - 1
        j = -1
        while len(path[j][0].keys) < min_keys:
            cur_node = path[j][0]
            cur_idx = path[j][1]
            if cur_idx == -1:   # root is underflow
                break
            parent = path[j-1][0]

            left_sibling = parent.children[cur_idx - 1] if cur_idx > 0 else None
            right_sibling = parent.children[cur_idx + 1] if cur_idx < len(parent.children) - 1 else None
            # Try Left Redistribution
            if left_sibling is not None and len(left_sibling.keys) > min_keys:
                sep_key = parent.keys[cur_idx - 1]
                sep_rid = parent.rids[cur_idx - 1]
                cur_node.keys.insert(0, sep_key)
                cur_node.rids.insert(0, sep_rid)
                parent.keys[cur_idx - 1] = left_sibling.keys[-1]
                parent.rids[cur_idx - 1] = left_sibling.rids[-1]
                del left_sibling.keys[-1], left_sibling.rids[-1]
                if not cur_node.is_leaf:
                    cur_node.children.insert(0, left_sibling.children[-1])
                    del left_sibling.children[-1]
            # Try Right Redistribution
            elif right_sibling is not None and len(right_sibling.keys) > min_keys:
                sep_key = parent.keys[cur_idx]
                sep_rid = parent.rids[cur_idx]
                cur_node.keys.append(sep_key)
                cur_node.rids.append(sep_rid)
                parent.keys[cur_idx] = right_sibling.keys[0]
                parent.rids[cur_idx] = right_sibling.rids[0]
                del right_sibling.keys[0], right_sibling.rids[0]
                if not cur_node.is_leaf:
                    cur_node.children.append(right_sibling.children[0])
                    del right_sibling.children[0]
            # Merge
            else:
                self.total_nodes -= 1
                # Try Left Merge
                if left_sibling is not None:
                    left_sibling.keys = left_sibling.keys + [parent.keys[cur_idx - 1]] + cur_node.keys
                    left_sibling.rids = left_sibling.rids + [parent.rids[cur_idx - 1]] + cur_node.rids
                    left_sibling.children += cur_node.children
                    del parent.keys[cur_idx - 1], parent.rids[cur_idx - 1], parent.children[cur_idx]
                # Try Right Merge
                elif right_sibling is not None:
                    cur_node.keys = cur_node.keys + [parent.keys[cur_idx]] + right_sibling.keys
                    cur_node.rids = cur_node.rids + [parent.rids[cur_idx]] + right_sibling.rids
                    cur_node.children += right_sibling.children
                    del parent.keys[cur_idx], parent.rids[cur_idx], parent.children[cur_idx + 1]
            j -= 1
        # clean root's children if there are no children for root
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.total_nodes -= 1
            self.root = self.root.children[0]

    def range_query(self, low, high):
        """Return list of (key, rid) pairs for all keys in [low, high]"""
        result = []
        self._range_helper(self.root, low, high, result)
        return result
    
    def _range_helper(self, node, low, high, result):
        i = 0
        while i < len(node.keys) and low > node.keys[i]:
            i += 1
        if not node.is_leaf:
            self._range_helper(node.children[i], low, high, result)
        while i < len(node.keys) and node.keys[i] <= high:
            result.append([node.keys[i], node.rids[i]])
            i += 1
            if not node.is_leaf:
                self._range_helper(node.children[i], low, high, result)

    def node_count(self):
        """Return total number of nodes (internal + leaf)."""
        return self.total_nodes

    def node_utilization(self):
        """Return average fill ratio across all nodes."""
        return self.total_keys / (self.total_nodes * (self.n - 1))
    
# B*-tree

class BStarTreeNode(BTreeNode):
    def __init__(self, is_leaf=False):
        super().__init__(is_leaf)


class BStarTree(BTree):
    """
    B*-tree: before splitting, attempt redistribution with a sibling.
    If both siblings are full, use 2-to-3 split strategy.
    """

    def __init__(self, n):
        super().__init__(n)
        self.root = BStarTreeNode(is_leaf=True)

    def insert(self, key, rid):
        """Insert (key, rid) into the appropriate leaf. Split as needed."""
        path = self._find_path(key)
        cur_node = path[-1][0]
        idx = 0
        while idx < len(cur_node.keys) and key > cur_node.keys[idx]:
            idx += 1
        cur_node.keys.insert(idx, key)
        cur_node.rids.insert(idx, rid)
        self.total_keys += 1
        
        # check overflow
        j = -1
        while j >= -len(path):
            cur_node = path[j][0]
            cur_idx = path[j][1]
            if len(cur_node.keys) == self.n:
                if cur_idx == -1:  # root
                    i = math.ceil(self.n / 2)
                    new_node = BStarTreeNode(is_leaf=cur_node.is_leaf)
                    self.total_nodes += 1
                    sep_key = cur_node.keys[i-1]
                    sep_rid = cur_node.rids[i-1]
                    new_node.keys = cur_node.keys[i:]
                    new_node.rids = cur_node.rids[i:]
                    del cur_node.keys[i-1:], cur_node.rids[i-1:]
                    if not cur_node.is_leaf:
                        new_node.children = cur_node.children[i:]
                        del cur_node.children[i:]
                    new_root = BStarTreeNode()
                    self.total_nodes += 1
                    new_root.keys = [sep_key]
                    new_root.rids = [sep_rid]
                    new_root.children = [cur_node, new_node]
                    self.root = new_root
                    self.split_count += 1
                    return 
                # try redistribution
                parent = path[j-1][0]
                left_sibling = parent.children[cur_idx - 1] if cur_idx > 0 else None
                right_sibling = parent.children[cur_idx + 1] if cur_idx < len(parent.children) - 1 else None

                if left_sibling is not None and len(left_sibling.keys) < self.n - 1:
                    combined_keys = left_sibling.keys + [parent.keys[cur_idx - 1]] + cur_node.keys
                    combined_rids = left_sibling.rids + [parent.rids[cur_idx - 1]] + cur_node.rids
                    mid = len(combined_keys) // 2

                    left_sibling.keys = combined_keys[:mid]
                    left_sibling.rids = combined_rids[:mid]
                    parent.keys[cur_idx - 1] = combined_keys[mid]
                    parent.rids[cur_idx - 1] = combined_rids[mid]
                    cur_node.keys = combined_keys[mid + 1:]
                    cur_node.rids = combined_rids[mid + 1:]
                    if not left_sibling.is_leaf:
                        combined_children = left_sibling.children + cur_node.children
                        left_sibling.children = combined_children[:mid + 1]
                        cur_node.children = combined_children[mid + 1:]
                    break
                elif right_sibling is not None and len(right_sibling.keys) < self.n - 1:
                    combined_keys = cur_node.keys + [parent.keys[cur_idx]] + right_sibling.keys
                    combined_rids = cur_node.rids + [parent.rids[cur_idx]] + right_sibling.rids
                    mid = len(combined_keys) // 2

                    cur_node.keys = combined_keys[:mid]
                    cur_node.rids = combined_rids[:mid]
                    parent.keys[cur_idx] = combined_keys[mid]
                    parent.rids[cur_idx] = combined_rids[mid]
                    right_sibling.keys = combined_keys[mid + 1:]
                    right_sibling.rids = combined_rids[mid + 1:]
                    if not right_sibling.is_leaf:
                        combined_children = cur_node.children + right_sibling.children
                        cur_node.children = combined_children[:mid + 1]
                        right_sibling.children = combined_children[mid + 1:]
                    break
                else:   # 2-to-3 split
                    new_node = BStarTreeNode(is_leaf=cur_node.is_leaf)
                    self.split_count += 1
                    self.total_nodes += 1
                    if left_sibling is not None:
                        combined_keys = left_sibling.keys + [parent.keys[cur_idx - 1]] + cur_node.keys
                        combined_rids = left_sibling.rids + [parent.rids[cur_idx - 1]] + cur_node.rids

                        total = len(combined_keys)
                        remain = total - 2  # excluding two seperators
                        base = remain // 3
                        extra = remain % 3

                        counts = [
                            base + (1 if extra > 0 else 0),
                            base + (1 if extra > 1 else 0),
                            base
                        ]

                        left_count, mid_count, right_count = counts
                        sep_idx1 = left_count
                        sep_idx2 = left_count + 1 + mid_count

                        left_sibling.keys = combined_keys[:sep_idx1]
                        left_sibling.rids = combined_rids[:sep_idx1]

                        sep_key1 = combined_keys[sep_idx1]
                        sep_rid1 = combined_rids[sep_idx1]

                        new_node.keys = combined_keys[sep_idx1 + 1:sep_idx2]
                        new_node.rids = combined_rids[sep_idx1 + 1:sep_idx2]

                        sep_key2 = combined_keys[sep_idx2]
                        sep_rid2 = combined_rids[sep_idx2]

                        cur_node.keys = combined_keys[sep_idx2 + 1:]
                        cur_node.rids = combined_rids[sep_idx2 + 1:]

                        # parent
                        parent.keys[cur_idx - 1] = sep_key1
                        parent.rids[cur_idx - 1] = sep_rid1
                        parent.keys.insert(cur_idx, sep_key2)
                        parent.rids.insert(cur_idx, sep_rid2)
                        parent.children.insert(cur_idx, new_node)

                        if not cur_node.is_leaf:
                            combined_children = left_sibling.children + cur_node.children
                            left_sibling.children = combined_children[:left_count + 1]
                            new_node.children = combined_children[left_count + 1:left_count + 1 + mid_count + 1]
                            cur_node.children = combined_children[left_count + 1 + mid_count + 1:]
                    elif right_sibling is not None:
                        combined_keys = cur_node.keys + [parent.keys[cur_idx]] + right_sibling.keys
                        combined_rids = cur_node.rids + [parent.rids[cur_idx]] + right_sibling.rids

                        total = len(combined_keys)
                        remain = total - 2  # excluding two seperators
                        base = remain // 3
                        extra = remain % 3

                        counts = [
                            base + (1 if extra > 0 else 0),
                            base + (1 if extra > 1 else 0),
                            base
                        ]

                        left_count, mid_count, right_count = counts
                        sep_idx1 = left_count
                        sep_idx2 = left_count + 1 + mid_count

                        cur_node.keys = combined_keys[:sep_idx1]
                        cur_node.rids = combined_rids[:sep_idx1]

                        sep_key1 = combined_keys[sep_idx1]
                        sep_rid1 = combined_rids[sep_idx1]

                        new_node.keys = combined_keys[sep_idx1 + 1:sep_idx2]
                        new_node.rids = combined_rids[sep_idx1 + 1:sep_idx2]

                        sep_key2 = combined_keys[sep_idx2]
                        sep_rid2 = combined_rids[sep_idx2]

                        right_sibling.keys = combined_keys[sep_idx2 + 1:]
                        right_sibling.rids = combined_rids[sep_idx2 + 1:]

                        # parent
                        parent.keys[cur_idx] = sep_key1
                        parent.rids[cur_idx] = sep_rid1
                        parent.keys.insert(cur_idx + 1, sep_key2)
                        parent.rids.insert(cur_idx + 1, sep_rid2)
                        parent.children.insert(cur_idx + 1, new_node)

                        if not cur_node.is_leaf:
                            combined_children = cur_node.children + right_sibling.children
                            cur_node.children = combined_children[:left_count + 1]
                            new_node.children = combined_children[left_count + 1:left_count + 1 + mid_count + 1]
                            right_sibling.children = combined_children[left_count + 1 + mid_count + 1:]
            j -= 1

    def delete(self, key):
        """Delete key from tree. Handle underflow by trying redistribution if failed merge."""
        if self.search(key) is None:    return
        path = []
        node = self.root
        path.append([node, -1])

        match_node = None
        match_idx = None

        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1
            if i < len(node.keys) and node.keys[i] == key:
                match_node = node
                match_idx = i
                break
            node = node.children[i]
            path.append([node, i])
        
        if match_node is None and node.is_leaf:
            if key in node.keys:
                match_node = node
                match_idx = node.keys.index(key)

        if match_node.is_leaf: # just delete it
            del_node = match_node
            del_idx = match_idx
        else:
            # find successor and swap it
            node = match_node.children[match_idx + 1]
            path.append([node, match_idx + 1])
            while not node.is_leaf:
                node = node.children[0]
                path.append([node, 0])
            successor = node
            # swap with successor
            match_node.keys[match_idx] = successor.keys[0]
            match_node.rids[match_idx] = successor.rids[0]
            del_node = successor
            del_idx = 0
        # delete key and rid in the leaf node
        del del_node.keys[del_idx], del_node.rids[del_idx]

        self.total_keys -= 1
        if len(path) == 1:  # Only root
            return
        
        self._repair_underflow_path(path)
        self._cleanup_root()
        
    def _repair_underflow_path(self, path):
        # Handle underflow
        min_keys = math.floor(2 * (self.n - 1) / 3)
        j = -1
        while len(path[j][0].keys) < min_keys:
            cur_node = path[j][0]
            cur_idx = path[j][1]
            if cur_idx == -1:   # root is underflow
                break
            parent = path[j-1][0]

            if parent is self.root and len(parent.children) == 2:
                left = parent.children[0]
                right = parent.children[1]

                combined_keys = left.keys + [parent.keys[0]] + right.keys
                combined_rids = left.rids + [parent.rids[0]] + right.rids

                if len(combined_keys) <= self.n - 1:
                    left.keys = combined_keys
                    left.rids = combined_rids
                    if not left.is_leaf:
                        left.children = left.children + right.children
                    self.root = left
                    self.total_nodes -= 2
                else:
                    total = len(combined_keys)

                    if cur_idx == 0:    # cur_node is left child, so give the left side at least min_keys if possible
                        sep_idx = max(min_keys, (total - 1) // 2)
                    else:   # cur_node is right child, so give the right side at least min_keys if possible
                        sep_idx = min((total - 1) // 2, total - 1 - min_keys)
                    
                    if sep_idx > self.n - 1:
                        sep_idx = self.n - 1
                    if total - sep_idx - 1 > self.n - 1:
                        sep_idx = total - 1 - (self.n - 1)

                    left.keys = combined_keys[:sep_idx]
                    left.rids = combined_rids[:sep_idx]
                    parent.keys[0] = combined_keys[sep_idx]
                    parent.rids[0] = combined_rids[sep_idx]
                    right.keys = combined_keys[sep_idx + 1:]
                    right.rids = combined_rids[sep_idx + 1:]

                    if not left.is_leaf:
                        combined_children = left.children + right.children
                        left.children = combined_children[:len(left.keys) + 1]
                        right.children = combined_children[len(left.keys) + 1:]
                break

            left_sibling = parent.children[cur_idx - 1] if cur_idx > 0 else None
            right_sibling = parent.children[cur_idx + 1] if cur_idx < len(parent.children) - 1 else None
            # Try Left Redistribution
            if left_sibling is not None and len(left_sibling.keys) > min_keys:
                combined_keys = left_sibling.keys + [parent.keys[cur_idx - 1]] + cur_node.keys
                combined_rids = left_sibling.rids + [parent.rids[cur_idx - 1]] + cur_node.rids
                mid = len(combined_keys) // 2
                
                left_sibling.keys = combined_keys[:mid]
                left_sibling.rids = combined_rids[:mid]
                parent.keys[cur_idx - 1] = combined_keys[mid]
                parent.rids[cur_idx - 1] = combined_rids[mid]
                cur_node.keys = combined_keys[mid + 1:]
                cur_node.rids = combined_rids[mid + 1:]
                if not cur_node.is_leaf:
                    combined_children = left_sibling.children + cur_node.children
                    left_sibling.children = combined_children[:mid + 1]
                    cur_node.children = combined_children[mid + 1:]
                break
            # Try Right Redistribution
            elif right_sibling is not None and len(right_sibling.keys) > min_keys:
                combined_keys = cur_node.keys + [parent.keys[cur_idx]] + right_sibling.keys
                combined_rids = cur_node.rids + [parent.rids[cur_idx]] + right_sibling.rids
                mid = len(combined_keys) // 2
                
                cur_node.keys = combined_keys[:mid]
                cur_node.rids = combined_rids[:mid]
                parent.keys[cur_idx] = combined_keys[mid]
                parent.rids[cur_idx] = combined_rids[mid]
                right_sibling.keys = combined_keys[mid + 1:]
                right_sibling.rids = combined_rids[mid + 1:]
                if not cur_node.is_leaf:
                    combined_children = cur_node.children + right_sibling.children
                    cur_node.children = combined_children[:mid + 1]
                    right_sibling.children = combined_children[mid + 1:]
                break
            else:
                if left_sibling is not None and right_sibling is not None:
                    start = cur_idx - 1
                elif cur_idx + 2 < len(parent.children):
                    start = cur_idx
                elif cur_idx >= 2:
                    start = cur_idx - 2
                else:
                    if left_sibling is not None:
                        combined_count = len(left_sibling.keys) + 1 + len(cur_node.keys)

                        if combined_count <= self.n - 1:
                            # 2-to-1 merge
                            left_sibling.keys = left_sibling.keys + [parent.keys[cur_idx - 1]] + cur_node.keys
                            left_sibling.rids = left_sibling.rids + [parent.rids[cur_idx - 1]] + cur_node.rids
                            if not cur_node.is_leaf:
                                left_sibling.children += cur_node.children
                            del parent.keys[cur_idx - 1], parent.rids[cur_idx - 1], parent.children[cur_idx]
                            self.total_nodes -= 1
                            j -= 1
                            continue
                        else:
                            # 2-node redistribution
                            combined_keys = left_sibling.keys + [parent.keys[cur_idx - 1]] + cur_node.keys
                            combined_rids = left_sibling.rids + [parent.rids[cur_idx - 1]] + cur_node.rids
                            
                            left_count = min(self.n - 1, (len(combined_keys) - 1) // 2)
                            right_count = len(combined_keys) - left_count - 1

                            if right_count > self.n - 1:
                                left_count = len(combined_keys) - 1 - (self.n - 1)

                            sep_idx = left_count

                            left_sibling.keys = combined_keys[:sep_idx]
                            left_sibling.rids = combined_rids[:sep_idx]
                            parent.keys[cur_idx - 1] = combined_keys[sep_idx]
                            parent.rids[cur_idx - 1] = combined_rids[sep_idx]
                            cur_node.keys = combined_keys[sep_idx + 1:]
                            cur_node.rids = combined_rids[sep_idx + 1:]
                            if not cur_node.is_leaf:
                                combined_children = left_sibling.children + cur_node.children
                                left_sibling.children = combined_children[:len(left_sibling.keys) + 1]
                                cur_node.children = combined_children[len(left_sibling.keys) + 1:]
                            break
                    elif right_sibling is not None:
                        combined_count = len(cur_node.keys) + 1 + len(right_sibling.keys)

                        if combined_count <= self.n - 1:
                            # 2-to-1 merge
                            cur_node.keys = cur_node.keys + [parent.keys[cur_idx]] + right_sibling.keys
                            cur_node.rids = cur_node.rids + [parent.rids[cur_idx]] + right_sibling.rids
                            if not cur_node.is_leaf:
                                cur_node.children += right_sibling.children
                            del parent.keys[cur_idx], parent.rids[cur_idx], parent.children[cur_idx + 1]
                            self.total_nodes -= 1
                            j -= 1
                            continue
                        else:
                            # 2-node redistribution
                            combined_keys = cur_node.keys + [parent.keys[cur_idx]] + right_sibling.keys
                            combined_rids = cur_node.rids + [parent.rids[cur_idx]] + right_sibling.rids
                            
                            left_count = min(self.n - 1, (len(combined_keys) - 1) // 2)
                            right_count = len(combined_keys) - left_count - 1

                            if right_count > self.n - 1:
                                left_count = len(combined_keys) - 1 - (self.n - 1)

                            sep_idx = left_count
                            cur_node.keys = combined_keys[:sep_idx]
                            cur_node.rids = combined_rids[:sep_idx]
                            parent.keys[cur_idx] = combined_keys[sep_idx]
                            parent.rids[cur_idx] = combined_rids[sep_idx]
                            right_sibling.keys = combined_keys[sep_idx + 1:]
                            right_sibling.rids = combined_rids[sep_idx + 1:]
                            if not cur_node.is_leaf:
                                combined_children = cur_node.children + right_sibling.children
                                cur_node.children = combined_children[:len(cur_node.keys) + 1]
                                right_sibling.children = combined_children[len(cur_node.keys) + 1:]
                            break
                a = parent.children[start]
                b = parent.children[start + 1]
                c = parent.children[start + 2]

                sep_idx1 = start 
                sep_idx2 = start + 1

                combined_keys = (
                    a.keys + [parent.keys[sep_idx1]] +
                    b.keys + [parent.keys[sep_idx2]] + 
                    c.keys
                )
                combined_rids = (
                    a.rids + [parent.rids[sep_idx1]] + 
                    b.rids + [parent.rids[sep_idx2]] + 
                    c.rids
                )
                capacity_for_3_to_2 = 2 * (self.n - 1) + 1
                if len(combined_keys) <= capacity_for_3_to_2:
                    left_count = min(self.n - 1, (len(combined_keys) - 1) // 2)
                    right_count = len(combined_keys) - left_count - 1

                    if right_count > self.n - 1:
                        left_count = len(combined_keys) - 1 - (self.n - 1)

                    sep_idx = left_count


                    a.keys = combined_keys[:sep_idx]
                    a.rids = combined_rids[:sep_idx]

                    parent.keys[sep_idx1] = combined_keys[sep_idx]
                    parent.rids[sep_idx1] = combined_rids[sep_idx]

                    b.keys = combined_keys[sep_idx + 1:]
                    b.rids = combined_rids[sep_idx + 1:]

                    if not cur_node.is_leaf:
                        combined_children = a.children + b.children + c.children
                        a.children = combined_children[:len(a.keys) + 1]
                        b.children = combined_children[len(a.keys) + 1:]

                    del parent.keys[sep_idx2], parent.rids[sep_idx2], parent.children[start + 2]
                    self.total_nodes -= 1
                else:
                    # 3-node redistribution
                    total = len(combined_keys)
                    node_total = total - 2

                    base = node_total // 3
                    extra = node_total % 3

                    counts = [
                        base + (1 if extra > 0 else 0),
                        base + (1 if extra > 1 else 0),
                        base
                    ]

                    a_count, b_count, c_count = counts

                    sep1 = a_count
                    sep2 = a_count + 1 + b_count

                    a.keys = combined_keys[:sep1]
                    a.rids = combined_rids[:sep1]
                    parent.keys[sep_idx1] = combined_keys[sep1]
                    parent.rids[sep_idx1] = combined_rids[sep1]
                    b.keys = combined_keys[sep1 + 1:sep2]
                    b.rids = combined_rids[sep1 + 1:sep2]
                    parent.keys[sep_idx2] = combined_keys[sep2]
                    parent.rids[sep_idx2] = combined_rids[sep2]
                    c.keys = combined_keys[sep2 + 1:]
                    c.rids = combined_rids[sep2 + 1:]
                    if not a.is_leaf:
                        combined_children = a.children + b.children + c.children
                        a.children = combined_children[:len(a.keys) + 1]
                        b.children = combined_children[len(a.keys) + 1:len(a.keys) + 1 + len(b.keys) + 1]
                        c.children = combined_children[len(a.keys) + 1 + len(b.keys) + 1:]
                    break
            j -= 1

    def _cleanup_root(self):
        # clean root's children if there are no children for root
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.total_nodes -= 1
            self.root = self.root.children[0]

    def range_query(self, low, high):
        """Return list of (key, rid) pairs for all keys in [low, high]"""
        result = []
        self._range_helper(self.root, low, high, result)
        return result
    
    def _range_helper(self, node, low, high, result):
        i = 0
        while i < len(node.keys) and low > node.keys[i]:
            i += 1
        if not node.is_leaf:
            self._range_helper(node.children[i], low, high, result)
        while i < len(node.keys) and node.keys[i] <= high:
            result.append([node.keys[i], node.rids[i]])
            i += 1
            if not node.is_leaf:
                self._range_helper(node.children[i], low, high, result)

    def node_count(self):
        """Return total number of nodes (internal + leaf)."""
        return self.total_nodes

    def node_utilization(self):
        """Return average fill ratio across all nodes."""
        return self.total_keys / (self.total_nodes * (self.n - 1))
    


# B+-tree

class BPlusInternalNode:
    def __init__(self):
        self.keys = []        # separator keys
        self.children = []    # child pointers (len == len(keys) + 1)


class BPlusLeafNode:
    def __init__(self):
        self.keys = []        # sorted keys
        self.rids = []        # rids[i] corresponds to keys[i]
        self.next = None      # pointer to next leaf (linked list)


class BPlusTree:
    def __init__(self, n):
        self.n = n
        self.root = BPlusLeafNode()
        self.split_count = 0
        self.total_nodes = 1
        self.total_records = 0
        self.total_key_slots = 0

    def _find_path(self, key):
        """Return the path from the root to correct place"""
        path = []
        node = self.root
        path.append([node, -1])
        while isinstance(node, BPlusInternalNode):
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
            path.append([node, i])
        return path
        

    def search(self, key):
        """Return RID if found, else None. Must always traverse to a leaf."""
        node = self._find_path(key)[-1][0]
        if key in node.keys:
            return node.rids[node.keys.index(key)]
        return None

    def insert(self, key, rid):
        """Insert (key, rid) into the appropriate leaf. Split as needed."""
        path = self._find_path(key)
        cur_node = path[-1][0]
        idx = 0
        while idx < len(cur_node.keys) and key >= cur_node.keys[idx]:
            idx += 1
        cur_node.keys.insert(idx, key)
        cur_node.rids.insert(idx, rid)
        self.total_records += 1
        self.total_key_slots += 1
        
        # Split occur!
        if len(cur_node.keys) == self.n:
            self.split_count += 1
            i = math.ceil(self.n/2)
            sep_key = cur_node.keys[i]
            new_node = BPlusLeafNode()
            self.total_nodes += 1
            new_node.keys = cur_node.keys[i:]
            new_node.rids = cur_node.rids[i:]
            del cur_node.keys[i:], cur_node.rids[i:]
            new_node.next = cur_node.next
            cur_node.next = new_node

            # Only root
            if len(path) == 1:
                new_root = BPlusInternalNode()
                self.total_nodes += 1
                new_root.keys = [sep_key]
                new_root.children = [cur_node, new_node]
                self.root = new_root
                self.total_key_slots += 1
                return 

            # Insert seperator key and new_node into the internal node's keys and children
            idx = 0
            j = -2
            while idx < len(path[j][0].keys) and sep_key >= path[j][0].keys[idx]:
                idx += 1
            path[j][0].keys.insert(idx, sep_key)
            path[j][0].children.insert(idx + 1, new_node)
            self.total_key_slots += 1
            # Check splits in internal nodes
            while isinstance(path[j][0], BPlusInternalNode) and len(path[j][0].keys) == self.n:
                self.split_count += 1
                sep_key = path[j][0].keys[i-1]
                new_node = BPlusInternalNode()
                self.total_nodes += 1
                new_node.keys = path[j][0].keys[i:]
                new_node.children = path[j][0].children[i:]
                del path[j][0].keys[i-1:], path[j][0].children[i:]

                if path[j][1] == -1:    # reached to the root
                    new_root = BPlusInternalNode()
                    self.total_nodes += 1
                    new_root.keys = [sep_key]
                    new_root.children = [self.root, new_node]
                    self.root = new_root
                    return 
                j -= 1
                idx = 0
                while idx < len(path[j][0].keys) and sep_key >= path[j][0].keys[idx]:
                    idx += 1
                path[j][0].keys.insert(idx, sep_key)
                path[j][0].children.insert(idx + 1, new_node)

    def delete(self, key):
        """Delete key from leaf. Handle underflow via merge or redistribution."""
        path = self._find_path(key)
        leaf = path[-1][0]
        if key not in leaf.keys: return # there is no such key in this tree
        pos = leaf.keys.index(key)
        del leaf.keys[pos], leaf.rids[pos]
        self.total_records -= 1
        self.total_key_slots -= 1
        if len(path) == 1:  # Only root
            return
        # Handle underflow
        min_keys = math.ceil((self.n - 1) / 2)
        j = -1
        while True:
            cur_node = path[j][0]
            cur_idx = path[j][1]
            if cur_idx == -1:   # root is underflow
                break
            if isinstance(cur_node, BPlusLeafNode):
                min_keys = math.ceil((self.n - 1) / 2)
            else:
                min_keys = math.ceil(self.n / 2) - 1
            if len(path[j][0].keys) >= min_keys:
                break
            parent = path[j-1][0]
            left_sibling = parent.children[cur_idx - 1] if cur_idx > 0 else None
            right_sibling = parent.children[cur_idx + 1] if cur_idx < len(parent.children) - 1 else None
            # Try Left Redistribution
            if left_sibling is not None and len(left_sibling.keys) > min_keys:
                if isinstance(cur_node, BPlusLeafNode):
                    cur_node.keys.insert(0, left_sibling.keys[-1])
                    del left_sibling.keys[-1]
                    cur_node.rids.insert(0, left_sibling.rids[-1])
                    del left_sibling.rids[-1]
                    parent.keys[cur_idx - 1] = cur_node.keys[0]
                elif isinstance(cur_node, BPlusInternalNode):
                    sep_parent = parent.keys[cur_idx - 1]
                    cur_node.keys.insert(0, sep_parent)
                    parent.keys[cur_idx - 1] = left_sibling.keys[-1]
                    del left_sibling.keys[-1]
                    cur_node.children.insert(0, left_sibling.children[-1])
                    del left_sibling.children[-1]
            # Try Right Redistribution
            elif right_sibling is not None and len(right_sibling.keys) > min_keys:
                if isinstance(cur_node, BPlusLeafNode):
                    cur_node.keys.append(right_sibling.keys[0])
                    del right_sibling.keys[0]
                    cur_node.rids.append(right_sibling.rids[0])
                    del right_sibling.rids[0]
                    parent.keys[cur_idx] = right_sibling.keys[0]
                elif isinstance(cur_node, BPlusInternalNode):
                    sep_parent = parent.keys[cur_idx]
                    cur_node.keys.append(sep_parent)
                    parent.keys[cur_idx] = right_sibling.keys[0]
                    del right_sibling.keys[0]
                    cur_node.children.append(right_sibling.children[0])
                    del right_sibling.children[0]
            # Merge
            else:
                self.total_nodes -= 1
                # Try Left Merge
                if left_sibling is not None:
                    if isinstance(cur_node, BPlusLeafNode):
                        left_sibling.keys += cur_node.keys
                        left_sibling.rids += cur_node.rids
                        left_sibling.next = cur_node.next
                        del parent.keys[cur_idx-1], parent.children[cur_idx]
                        self.total_key_slots -= 1
                    elif isinstance(cur_node, BPlusInternalNode):
                        left_sibling.keys = left_sibling.keys + [parent.keys[cur_idx - 1]] + cur_node.keys
                        left_sibling.children += cur_node.children
                        del parent.keys[cur_idx - 1], parent.children[cur_idx]
                # Try Right Merge
                elif right_sibling is not None:
                    if isinstance(cur_node, BPlusLeafNode):
                        cur_node.keys += right_sibling.keys
                        cur_node.rids += right_sibling.rids
                        cur_node.next = right_sibling.next
                        del parent.keys[cur_idx], parent.children[cur_idx + 1]
                        self.total_key_slots -= 1
                    elif isinstance(cur_node, BPlusInternalNode):
                        cur_node.keys = cur_node.keys + [parent.keys[cur_idx]] + right_sibling.keys
                        cur_node.children += right_sibling.children
                        del parent.keys[cur_idx], parent.children[cur_idx + 1]
            j -= 1
        # clean root's children if there are no children for root
        if isinstance(self.root, BPlusInternalNode) and len(self.root.keys) == 0:
            self.total_nodes -= 1
            self.root = self.root.children[0]

    def range_query(self, low, high):
        """Return list of (key, rid) pairs for all keys in [low, high]"""
        low_path = self._find_path(low)
        leaf = low_path[-1][0]
        result = []
        while leaf is not None:
            for k, r in zip(leaf.keys, leaf.rids):
                if k > high:
                    return result
                elif low <= k:
                    result.append((k, r))
            leaf = leaf.next
        return result

    def node_count(self):
        """Return total number of nodes (internal + leaf)."""
        return self.total_nodes

    def node_utilization(self):
        """Return average fill ratio across all nodes."""
        return self.total_key_slots / (self.total_nodes * (self.n - 1))

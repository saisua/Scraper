from typing import Dict, Iterable, Any, Tuple, List
from random import choice

def main():
    b1 = BinaryTree()
    b2 = BinaryTree({"Test1":[1,2,3], "Test2":[5,6,7]})

    b1.append(["What's up"], compare=3, multiple_compares=range(10))

    print(b1.find(5)[1].values)

# Should I move this structure so that it can be used anywhere?
class BinaryTree:
    root:"Node"=None
    length:int = 0

    def __init__(self, data:Dict[Any, Iterable["Comparable"]]={}, central_point:"Comparable"=None):
        if(not central_point is None):
            self.root = self.add_pivot(central_point)
        elif(len(data)):
            v, c_list = data.popitem()

            if(isinstance(c_list, list)):
                c_iter = iter(c_list)
                self.root = self.Node(None, None, values=list(v), compare=next(c_iter), 
                                        multiple_compares=set(c_list))
                self.length = 1

                for compare in c_iter:
                    self.append(values=list(v), compare=compare, multiple_compares=set(c_list))
            else:
                self.root = self.Node(None, None, values=list(v), compare=set(c_list))
                self.length = 1

        for v, c_list in data.items():
            if(isinstance(c_list, list)):
                for compare in c_list:
                    self.append(values=list(v), compare=compare, multiple_compares=c_list)
            else:
                self.append(values=list(v), compare=c_list)

    def __len__(self):
        return self.length

    def __str__(self):
        return ','.join(self.__recursive_str(self.root) if self.root else '')

    def __recursive_str(self, node):
        if(node.left or node.right): 
            result = []
            if(node.left):
                result.extend(self.__recursive_str(node.left))
            if(node.right): 
                return result + self.__recursive_str(node.right)

            return result
            
        elif(node.compare): return [str(node.compare)]
        

        return result

    def find(self, compare:"Comparable") -> Tuple[bool, object]:
            if(not self.root):
                return (False, None)

            last_node = node = self.root

            while(node := (node.left if compare < node.compare else node.right)):
                #print("left" if compare < node.compare else "right", end=', ')
                last_node = node
            #print()

            return (compare == last_node.compare or compare in last_node.multiple_compares,
                    last_node)

    def find_append(self, compare) -> Tuple[bool, object]:
        if(not self.root):
            return (False, None)

        last_node = node = self.root
        mid = None

        while(node := (node.left if compare < node.compare else node.right)):
            if(not node.locked and (right := node.right) and (left := node.left)):
                if(left.compare < compare < right.compare):
                    mid = choice(right,left)
                    break
            last_node = node

        # End search
        if(node):
            while(node := (node.left if compare < node.compare else node.right)):
                last_node = node

        found = (compare == last_node.compare or 
                (last_node.multiple_compares and 
                compare in last_node.multiple_compares))

        return (found,
                last_node if found else mid or last_node)

    def append(self, values:List[Any], compare:"Comparable", *, 
                multiple_compares:Iterable={}, locked:bool=False) -> None:
        #print(f"Add {compare=}")
        if(not self.root):
            self.root = self.Node(None, None, values=values, compare=compare, 
                                    multiple_compares=multiple_compares, 
                                    locked=locked)
            return

        match, node = self.find_append(compare)

        if(match):
            # Not doing an n^2 unique comprobation since most of the time,
            # it won't even matter
            if(not values[0] in node.values):
                if(multiple_compares != node.multiple_compares):
                    node.multiple_compares.update(set(multiple_compares))
                node.values.extend(values)
        else:
            compared = compare < node.compare
            
            if(node.locked and ((compared and not node.left) or not (compared or node.right))):
                new_node = self.Node(node, compared,
                                    values=values, compare=compare,
                                    multiple_compares=multiple_compares, 
                                    locked=locked)

                if(compared):
                    node.left = new_node
                else:
                    node.rigth = new_node

            elif(node.locked or not (node.right and node.left) and (node.right or node.left)):
                new_node = self.Node(node, compared,
                                    values=values, compare=compare,
                                    multiple_compares=multiple_compares, 
                                    locked=locked)

                if(compared):
                    last = node.left
                    node.left = new_node
                else:
                    last = node.rigth
                    node.rigth = new_node

                if(last):
                    self.append(last)
            else:
                new_pivot = self.Node(node.parent, node.rel_lower, 
                                    locked=locked)

                if(node.parent):
                    if(node.rel_lower): node.parent.left = new_pivot
                    else: node.parent.right = new_pivot
                else:
                    self.root = new_pivot

                node.parent = new_pivot


                if(compared):
                    new_pivot.compare = node.compare
                    node.rel_lower = False

                    new_pivot.left = self.Node(node, True, values=values, compare=compare, 
                                            multiple_compares=multiple_compares)
                    new_pivot.right = node
                else:
                    new_pivot.compare = compare
                    node.rel_lower = True

                    new_pivot.left = node
                    new_pivot.right = self.Node(node, False, values=values, compare=compare, 
                                            multiple_compares=multiple_compares)
                

        self.length += 1
    
    def __getitem__(self, item:"Comparable") -> Tuple[bool, object]:
        return self.find(item)


    def add_pivot(self, compare:"Comparable", *, locked=True):
        self.append(None, compare=compare, locked=locked)

    ## Since I dont't have any need to remove Nodes, I'm not adding that

    class Node:
        parent:"Node"
        left:"Node"
        right:"Node"
        values:List[Any]
        compare:"Comparable"
        multiple_compares:Iterable["Comparables"]

        # Only useful if all parent nodes are also locked
        locked:bool=False

        # Parent relationship. Is it lower?
        rel_lower:bool

        def __init__(self, parent:"Node", rel_lower:bool, *, left:"Node"=None, right:"Node"=None, 
                        values:List[Any]=None, compare:"Comparable"=None,
                        locked:bool=False, multiple_compares:Iterable["Comparable"]=list()):
            self.values = values or []
            self.compare = compare
            self.multiple_compares = multiple_compares

            self.left = left
            self.right = right
            
            self.locked = locked

            self.parent = parent
            self.rel_lower = rel_lower


if __name__ == "__main__":
    main()
#from spacy.kb import KnowledgeBase
#import spacy.kb
from spacy.language import Language
from spacy.tokens import Token, Span
from spacy.tokens.doc import Doc
# Hash comparison 4 performance reasons
from spacy.symbols import (PERSON, DET, PRON, nsubj, VERB, aux, prep, 
                            pcomp, pobj, dobj, relcl, NOUN)
#
from spacy import displacy
import spacy
import neuralcoref
#from neuralcoref import neuralcoref

#neuralcoref.add_to_pipe()
#print(dir(neuralcoref))
#print(dir(neuralcoref.__init__))

import re
from collections import defaultdict
from typing import Union, ByteString, AnyStr
from datetime import datetime


try:
    from Structures.Knowledge_tmp import Knowledge
    from Structures.Span_BinaryTree_tmp import BinaryTree

except ModuleNotFoundError:
    from .Structures.Knowledge_tmp import Knowledge
    from .Structures.Span_BinaryTree_tmp import BinaryTree


def main():
    timings = dict()

    print("Loading Language... ",end='')
    
    timings["Language loading"] = datetime.now()
    t = Text_analizer("en_core_web_md", knowledge_kwargs={"location_lookup":False})
    
    print("Done")
    text = False
    #text = "My friend Dan is in the UK. He is awesome. Dan is looking for you."
    #text = "The Mona Lisa is really beautiful. I'm going to see her real soon."
    #text = "My new company, the one I told you about, is looking at buying a UK startup for $1 billion"
    
    print("Text loading"); timings["Text loading"] = datetime.now()
    if(not text): 
        with open(f"{'//'.join(__file__.split('/')[:-1]) or '.'}//test3.txt",'r',encoding="utf-8") as f:
            text = f.read()
    #print("2")

    print("Text analysis"); timings["Text analysis"] = datetime.now()
    doc = t.text_analysis(text)

    if(False):
        timings["Displacy usage"] = datetime.now()
        displacy.serve(doc)

    do = print

    do("Subject analysis"); timings["Subject analysis"] = datetime.now()
    t.subj_analysis(doc)
    do("Coreference analysis"); timings["Coreference analysis"] = datetime.now()
    t.coref_analysis(doc)
    do("Entity analysis"); timings["Entity analysis"] = datetime.now()
    t.entity_analysis(doc)
    do("Verb analysis"); timings["Verb analysis"] = datetime.now()
    t.verb_analysis(doc)
    do("Statement analysis\n"); timings["Statement analysis"] = datetime.now()
    t.statement_analysis(doc)
    timings["END"] = datetime.now()


    repl = re.compile('\s([^($[{\w])')

    print()
    print(doc)
    print(repl.sub('\g<1>', ' '.join(map(str, doc._.coref_resolved_list))))
    print()

    print("\n### RESULTS ###")

    final_statements = set()

    for verbs in t.knowledge.verbs.values():
        for verb_span in verbs:
            i = verb_span._.information
            #debug_s = i["statements"]
            if(not len(i["subject"]._.information["entities"])):
                continue

            for statement in i["statements"]:
                final_statements.add(f"- {i['subject']} {verb_span} {statement}")

    for s in final_statements:
        print(s.strip())

    print("###############\n")

    last_name = None
    last_time = None
    for name, time in timings.items():
        if(last_name):
            print(f"{last_name} ({(lambda t: t.seconds+(t.microseconds/1000000))(time-last_time)} sec.)")
        last_name = name
        last_time = time

    print("\nEND 0")

def store(name:str, data:Union[ByteString, AnyStr], *, mode:str='w') -> None:
    with open(f"{__file__[-2]}//Results//TextAnalysis//{name}", mode) as file:
        file.write(data)

class Text_analizer:
    #cdef object nlp_obj
    nlp_obj:Language

    knowledge:Knowledge

    #def __cinit__(self, model:str):
    def __init__(self, model:str, *, knowledge_kwargs):
        self.nlp_obj = spacy.load(model)
        neuralcoref.add_to_pipe(self.nlp_obj)

        self.knowledge = Knowledge(**knowledge_kwargs)

    def text_analysis(self, text:str) -> Doc:
        doc = self.nlp_obj(text)
        self.knowledge.subjects.add_pivot(len(doc)//2)

        # So that other BinaryTrees can benefit from pivot
        Knowledge.subjects = self.knowledge.subjects

        return doc

    def pattern_analysis(self, doc:Doc, pattern:re.Pattern) -> Doc:
        raise NotImplementedError

    def subj_analysis(self, doc:Doc) -> Doc:
        if(not "subjects" in doc._.information):
            doc._.information["subjects"] = self.knowledge.subjects
        if(not "verbs" in doc._.information):
            doc._.information["verbs"] = []

        for subj in filter(lambda tok: tok.dep == nsubj, doc):
            children = aux = list(subj.children)
            s_start = s_end = subj.i

            #print(subj)
            #debug_path = [subj]

            # Look for starting token in subj
            if(len(aux)):
                aux = aux[0]
                while((aux_child := aux).i < s_start):
                    s_start = aux_child.i

                    try:
                        aux = next(aux_child.children)
                    except StopIteration:
                        break

                #debug_path.insert(0, doc[s_start])

            aux = children

            # Look for last token in subj
            while(len(aux) and (aux_child := aux[-1]).i > s_end):
                s_end = aux_child.i
                aux = list(aux_child.children)

                #debug_path.append(doc[s_end])

            #print(" > ".join(map(str, debug_path)))

            subj_span = doc[s_start:s_end+1]

            if(not subj_span.lemma_ in self.knowledge.subjects_set):
                print(f"[+] Subject {subj_span}")

            subj._.information["subject"] = subj_span
            subj_span._.information["references"] = []
            subj_span._.information["entities"] = []
            self.knowledge.subjects.append([subj_span], compare=s_start, 
                                            multiple_compares=range(s_start, s_end+1))
            self.knowledge.subjects.append([subj_span], compare=s_end, 
                                            multiple_compares=range(s_start, s_end+1))
            self.knowledge.subjects_set.add(subj_span.lemma_)

            try:
                verb = next(subj.ancestors)

                doc._.information["verbs"].append(verb)
                verb._.information["subject"] = subj_span
            except StopIteration:
                pass

            
        return doc


    #cpdef object coref_analysis(self, string text):
    def coref_analysis(self, doc:Doc) -> Doc:
        #cdef object tmp_doc = self.nlp_obj(text)
        tmp_list = list(doc)

        #cdef int resolution_offset = 0
        resolution_offset = 0

        for coref_cluster in doc._.coref_clusters:
            gender_unknown = True

            main = coref_cluster.main
            main_size = main.end-main.start

            if(not "entities" in main._.information):
                main._.information["entities"] = []

            check, subj_span = self.knowledge.subjects[main.start]
            if(check):
                subj_span._.information["references"].append(main)
            
            for mention in coref_cluster.mentions:
                if(mention.lower_ == main.lower_): continue

                ### Coreference resolution
                for token_index in range(mention.start, mention.end):
                    tmp_list.pop(mention.start+resolution_offset)
                for main_index in range(main_size):
                    tmp_list.insert(mention.start+main_index+resolution_offset, 
                                    doc[main.start+main_index])

                resolution_offset += main_size - (mention.end-mention.start)

                ### Gender extraction
                if(gender_unknown):
                    gender_unknown = self.knowledge.coref_gender_extraction(main, mention)
        ############

        doc._.coref_resolved_list = tmp_list

        return doc

    def entity_analysis(self, doc:Doc) -> Doc:
        self.knowledge.analize_entities(doc)

        return doc

    def verb_analysis(self, doc:Doc) -> Doc:
        for verb in doc._.information["verbs"]:
            span_min = span_max = verb.i

            for child in verb.children:
                if(child.dep == aux):
                    if(child.i < span_min):
                        span_min = child.i
                elif(child.dep == prep):
                    sub_children = list(child.children)
                    if(len(sub_children)):
                        for sub_child in filter(lambda sub: sub.dep in {pcomp}, sub_children):
                            if(span_max < sub_child.i):
                                span_max = sub_child.i
            ####################

            verb_span = doc[span_min:span_max+1]

            verb._.information["span"] = verb_span

            verb_span._.information["subject"] = verb._.information["subject"]
            verb_span._.information["verb"] = verb
            verb_span._.information["statements"] = []

            if(not verb_span.lemma_ in self.knowledge.verbs):
                print(f"[+] Verb {verb_span}")

            self.knowledge.verbs[verb_span.lemma_].append(verb_span)


        return doc

    def statement_analysis(self, doc:Doc) -> Doc:
        for obj in filter(lambda tok: tok.dep in {pobj,dobj}, doc):
            children = aux = list(obj.children)
            st_start = st_end = obj.i

            try:
                parent = next(obj.ancestors)
            except StopIteration:
                parent = None

            #print(subj)
            #debug_path = [subj]

            # Look for starting token in statement
            if(parent and parent.pos != VERB):
                while(parent and parent.pos != VERB):
                    st_start = parent.i
                    try:
                        parent = next(parent.ancestors)
                    except StopIteration:
                        parent = None
            elif(len(aux)):
                    aux = aux[0]
                    while((aux_child := aux).i < st_start):
                        st_start = aux_child.i

                        try:
                            aux = next(aux_child.children)
                        except StopIteration:
                            break

                #debug_path.insert(0, doc[s_start])


            aux = children

            # Look for last token in statement
            while(len(aux) and (aux_child := aux[-1]).i > st_end):
                st_end = aux_child.i
                aux = list(aux_child.children)


            state_span = doc[st_start:st_end+1]

            aux = parent
            while(aux and aux.pos != NOUN):
                try:
                    parent = aux
                    aux = next(parent.ancestors)
                except StopIteration:
                    break

            if(parent and (verb_span := parent._.information.get("span"))):
                verb_span._.information["statements"].append(state_span)

            print(f"[+] Statement {state_span}")

        return doc

if __name__ == "__main__":
    main()

from triggerowl.PrologForMuilty import PrologMT
import re


# put all rules into a dictionary where rule name is the key
def get_rules(filename):
    all_rules = {}
    rule_file = open(filename, "r")
    pattern = re.compile(r'rule\(.*?\.')
    rules = pattern.findall(rule_file.read())
    rule_file.close()
    for rule in rules:
        findObject = re.search(r'rule\(\'(.*?)\',(.*?])', rule, re.M | re.I)
        name = findObject.group(1)
        confidence = findObject.group(2).replace(' ', '')
        pattern = re.compile(r'pred\((.*?)\)')
        terms = pattern.findall(rule)
        lhs_raw = terms[:-1]
        rhs_raw = terms[-1]
        lhs = []
        for ante in lhs_raw:
            t = ante.split(",")
            fn = t[0].replace("'", "")
            fv = t[1].replace("'", "")
            fi = t[2].replace("'", "")
            lhs.append((fn, fv, fi))

        temp = rhs_raw.split(",")
        fnr = temp[0].replace("'", "")
        fvr = temp[1].replace("'", "")
        fir = temp[2].replace("'", "")

        all_rules[name] = (lhs, confidence, (fnr, fvr, fir))
    return all_rules


def pred_string(raw):
    searchObject = re.search(r'pred\((.*?),\s(.*?),\s(.*?)\)', str(raw), re.M | re.I)
    fact = searchObject.group(1)
    value = searchObject.group(2)
    impact = searchObject.group(3)
    if impact != '0':
        impact = "'" + impact + "'"
    result = "pred('" + fact + "','" + value + "'," + impact + ")"
    return result


# transform likelihood form "[X, X, X, X]" to string format like 'Definite' and 'VeryUnlikely'
def tran_vec_to_str(raw):
    if raw == "[0,0,0,0]":
        result = "Definite"
    elif raw == "[1,0,0,0]":
        result = "VeryUnlikely"
    elif raw == "[0,1,0,0]":
        result = "Unlikely"
    elif raw == "[0,0,1,0]":
        result = "Likely"
    else:
        result = "VeryLikely"
    return result


# transform likelihood form "[X,X,X,X]" to "<VU=X, U=X, L=X, V=X>"
def tran_vec(raw):
    if raw == "[0,0,0,0]":
        result = "Definite"
    else:
        cl = raw[1: -1].split(",")
        result = "<VU=" + cl[0] + ", U=" + cl[1] + ", L=" + cl[2] + ", V=" + cl[3] + ">"
    return result


# transform likelihood form "<VU=X, U=X, L=X, V=X>" to [X,X,X,X]
def tran_str(raw):
    searchObject = re.search(r'<VU=(\d).*?(\d).*?(\d).*?(\d)', raw, re.M | re.I)
    if searchObject:
        vu = int(searchObject.group(1))
        u = int(searchObject.group(2))
        l = int(searchObject.group(3))
        v = int(searchObject.group(4))
    else:
        vu = u = l = v = 0
    return [vu, u, l, v]


def add_str(rawList):
    s = [0, 0, 0, 0]
    for raw in rawList:
        CLStr = tran_str(raw)
        s = [s[0]+CLStr[0], s[1]+CLStr[1], s[2]+CLStr[2], s[3]+CLStr[3]]
    return "<VU="+str(s[0])+" ,U="+str(s[1])+" ,L="+str(s[2])+" ,V="+str(s[3])+">"


# # arrange the results into appropriate format for prototype to read
def get_chain(facts, first_given_facts_raw, rule_list, result_file):
    results = []
    idx = 0
    first_given_facts = set()
    fact_in_chain = set()
    for gf in first_given_facts_raw:
        gfObject = re.search(r'fact\(pred\((.*?)\)', gf, re.M | re.I)
        gf_raw = gfObject.group(1)
        g_raw = gf_raw.replace("'", "").split(",")
        gfn = g_raw[0]
        gfv = g_raw[1]
        gfi = g_raw[2]
        first_given_facts.add(gfn + gfv + gfi)
        fact_in_chain.add(gfn + gfv)

    fin_list = []
    inf_list = []
    all_inf_hash = set()
    for fact in reversed(facts):
        file = open(result_file[:-4] + "_" + str(idx) + ".txt", 'w')
        check_fact = {}
        cl_dict = {}
        inf_hash = set()
        searchObject = re.search(r'fact\(pred\((.*?)\),(\[.*?\]),\[(.*?\]\])\],(.*?)\],(.*?)\)', fact, re.M | re.I)
        if searchObject:
            conclusion_raw = searchObject.group(1)
            confidence_raw = searchObject.group(2)
            given_fact_raw = searchObject.group(3)
            missing_fact_raw = searchObject.group(4)
            rules_raw = searchObject.group(5)

            conc_raw = conclusion_raw.replace("'", "").split(",")
            cn = conc_raw[0]
            cv = conc_raw[1]
            ci = conc_raw[2]
            conc_cl = tran_vec(confidence_raw)

            check_fact['name'] = cn
            check_fact['state'] = cv
            check_fact['factliki0'] = conc_cl

            final_fact = "Final Facts, (Name: " + cn + "), (Value: " + cv + "), (Intensity: " + ci + \
                         "), (Likelihood:" + conc_cl + "), (Given facts: ("

            fact_pattern = re.compile(r'(\[pred.*?]])')
            fact_cl = fact_pattern.findall(given_fact_raw)

            check_fact['given_list'] = []
            for fc in fact_cl:
                temp = fc[6:-1].split(",[")
                f = temp[0][:-1].replace("'", "").split(",")
                fn = f[0]
                fv = f[1]
                cl = "[" + temp[1]
                c_re = tran_vec(cl)
                cl_dict[fn + " " + fv] = c_re
                final_fact += "\"" + fn + " " + fv + "\" "
                check_fact['given_list'].append(fn + " " + fv)

            final_fact = final_fact[:-1] + ")), (Missing facts: ("

            rule_pattern = re.compile(r'\[(\'.*?\[.*?\])\]')
            rule_cl = rule_pattern.findall(rules_raw)
            rules = []
            for r in rule_cl:
                rules.append(r.split(',')[0].replace('\'', ''))

            check_fact['missing_list'] = []
            if missing_fact_raw != "[":
                mfPattern = re.compile(r'pred\((.*?)\)')
                mfs = mfPattern.findall(missing_fact_raw)
                for mf_raw in mfs:
                    mf = mf_raw.replace("'", "").split(",")
                    mfn = mf[0]
                    mfv = mf[1]
                    final_fact += "\"" + mfn + " " + mfv + "\" "
                    fact_in_chain.add(mfn + mfv)
                    check_fact['missing_list'].append(mfn + " " + mfv)
                final_fact = final_fact[:-1] + ")), (NoMF: " + str(len(mfs)) + ")"
            else:
                final_fact += ")), (NoMF: 0)"

            tail = ""
            path_dict = {}
            for name in reversed(rules):
                result = ""
                rule_name = name.replace("'", "")
                rule = rule_list[rule_name]
                lhs_raw = rule[0]
                confidence = tran_vec_to_str(rule[1])
                rhs_raw = rule[2]

                cl_list = []
                given_missing_list = []
                check_infer_list = []
                for ante in lhs_raw:
                    fn = ante[0]
                    fv = ante[1]
                    antecedent = fn + " " + fv
                    if antecedent in check_fact['given_list']:
                        given_missing_list.append(antecedent)
                        cl = cl_dict[antecedent]
                        result += "Process " + antecedent + " (" + cl + ")" + " + "
                    elif antecedent in check_fact['missing_list']:
                        given_missing_list.append(antecedent)
                        result += "Process " + fn + " " + fv + " (Definite)" + " + "
                    else:
                        cl = path_dict[antecedent][1]
                        check_infer_list.append(antecedent)
                        result += "Process " + antecedent + " (" + cl + ")" + " + "

                path_rules = []
                for infer in check_infer_list:
                    for g in path_dict[infer][0]:
                        if g not in given_missing_list:
                            given_missing_list.append(g)
                    for r in path_dict[infer][2]:
                        if r not in path_rules:
                            path_rules.append(r)

                path_rules.append(rule_name)
                for i in path_rules:
                    r = rule_list[i]
                    cl_list.append(tran_vec(r[1]))

                for g in given_missing_list:
                    if g in cl_dict:
                        cl_list.append(cl_dict[g])

                for g in given_missing_list:
                    tail += "\"" + g + "\" "
                tail = tail[:-1]
                cn = rhs_raw[0]
                cv = rhs_raw[1]
                cl = add_str(cl_list)
                path_dict[cn + " " + cv] = [given_missing_list, cl, path_rules]
                result = result[:-3] + " -> " + rule_name[:-2] + ":" + confidence + " -> " + \
                         "Process " + cn + " " + cv + " (" + cl + ");(" + tail + ")"
                file.write(result+"\n")
                if result not in all_inf_hash:
                    all_inf_hash.add(result)
                    inf_list.append(result)
            fin_list.append(final_fact)
            file.write(final_fact+"\n")
            file.close()
            inf_hash.clear()
            idx += 1
            results.append(check_fact)
        else:
            searchObject = re.search(r'fact\(pred\((.*?)\),(\[.*?\])', fact, re.M | re.I)
            conclusion_raw = searchObject.group(1)
            confidence_raw = searchObject.group(2)

            conc_raw = conclusion_raw.replace("'", "").split(",")
            cn = conc_raw[0]
            cv = conc_raw[1]
            ci = conc_raw[2]
            conc_cl = tran_vec(confidence_raw)

            final_fact = "Final Facts, (Name: " + cn + "), (Value: " + cv + "), (Intensity: " + ci + \
                         "), (Likelihood:" + conc_cl + "), (Given facts: (\"" + cn + " " + cv + \
                         "\")), (Missing facts: ()), (NoMF: 0)"
            fin_list.append(final_fact)
        main_file = open(result_file, 'w')
        for rule in inf_list:
            main_file.write(rule+"\n")
        for fact in reversed(fin_list):
            main_file.write(fact+"\n")
        main_file.close()
    return results


# call prolog for inference
def get_results(rulefile, factfileName, resultfile):
    all_rules = get_rules(rulefile)
    all_results = []
    prolog = PrologMT()
    prolog.consult(rulefile)
    prolog.consult('Inference/atuRules/knowledge_base.pl')

    factfile = open(factfileName, 'r')
    first_given_facts = []
    for line in factfile.readlines():
        if len(line) != '\n':
            initial_fact = line.replace('\n', '')
            first_given_facts.append(initial_fact)
    fact_list = []

    for fact in first_given_facts:
        prolog.asserta(fact)

    flag = True
    pre_fact_list = []
    case = 0
    while flag:
        mf_length_dict = {}
        for soln in prolog.query("findgoal(Goal,CL,GF,MF,RL)."):
            # for soln in prolog.query("find(pred(N,V,I),CL)."):
            fact = soln["Goal"]
            cl = soln["CL"]
            gf = soln["GF"]
            mf = soln["MF"]
            rl = soln["RL"]
            fact_str = pred_string(fact)
            final_fact = "fact(" + fact_str + ","
            final_fact += str(cl).replace(' ', '')
            final_fact += ",["

            if len(gf) != 0:
                for fact in gf:
                    final_fact += "[" + pred_string(fact[0]) + ","
                    final_fact += str(fact[1]).replace(' ', '') + "],"
                final_fact = final_fact[:-1] + "],["
            else:
                final_fact = final_fact + "],["

            if len(mf) != 0:
                for fact in mf:
                    final_fact += pred_string(fact) + ","
                final_fact = final_fact[:-1] + "],["
            else:
                final_fact = final_fact + "],["

            if len(rl) != 0:
                for rule in rl:
                    final_fact += "['" + str(rule[0]) + "',"
                    final_fact += str(rule[1]).replace(' ', '') + "],"
                final_fact = final_fact[:-1] + "])"
            else:
                final_fact = final_fact + "])"

            try:
                old_len = mf_length_dict[fact_str]
                if old_len > len(mf):
                    mf_length_dict[fact_str] = len(mf)
            except:
                mf_length_dict[fact_str] = len(mf)

            fact_list.append((final_fact,fact_str,len(mf)))

        case += 1
        if len(fact_list) != len(pre_fact_list):
            pre_fact_list = fact_list
            prolog.retractall('fact(_,_,_,_,_)')
            for fact in fact_list:
                prolog.asserta(fact[0])
            # if case == 15:
            #     flag = False
            #     final_fact_list = []
            #     prolog.retractall('fact(_,_,_,_,_)')
            #     for fact in fact_list:
            #         pred = fact[1]
            #         shortest = mf_length_dict[pred]
            #         if fact[2] == shortest:
            #             final_fact_list.append(fact[0])
            #     all_results = get_chain(final_fact_list, first_given_facts, all_rules, resultfile)
            fact_list = []
        else:
            flag = False
            final_fact_list = []
            prolog.retractall('fact(_,_,_,_,_)')
            for fact in fact_list:
                pred = fact[1]
                shortest = mf_length_dict[pred]
                if fact[2] == shortest:
                    final_fact_list.append(fact[0])
            all_results = get_chain(final_fact_list, first_given_facts, all_rules, resultfile)
    return all_results


def run(verbose=True):

    facts = []
    facts.append('fact(pred(\'RoadType\',\'A\',0),[0,0,0,0],[],[],[])')
    facts.append('fact(pred(\'TrafficLoad\',\'Active\',0),[0,0,0,0],[],[],[])')
    facts.append('fact(pred(\'RoadCracking\',\'Active\',0),[0,0,0,0],[],[],[])')
    facts.append('fact(pred(\'RoadCrackingDepth\',\'Medium\',0),[0,0,0,0],[],[],[])')
    facts.append('fact(pred(\'Cracks\',\'Active\',0),[0,0,0,0],[],[],[])')

    results = get_results('Inference/atuRules/rules.pl', facts, 'Inference/test.txt')
    for i in results[1]:
        print(i)
    for i in results[0]:
        print(i)

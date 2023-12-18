#ifdef UNDEFVERBOSE
#undef VERBOSE
#endif

int n = 0;

static int ph (int p, int h) {
    assert (0 <= p), assert (p < n + 1);
    assert (0 <= h), assert (h < n);
    return 1 + h * (n+1) + p;
}

static int pigeon_id (int lit) {
    int idx = abs (lit);
    return ((idx - 1) % (n + 1));
}

static int hole_id (int lit) {
    int idx = abs (lit);
    return (int)floor((idx - 1)/(n + 1));
}

static bool has_lit(const std::deque<std::vector<int>> & current_trail, int lit) {
    for (auto level_lits : current_trail) {
        if(std::find(level_lits.begin(), level_lits.end(), lit) != level_lits.end()) {
            return true;
        }
    }
    return false;
}

class SymmetryBreaker : CaDiCaL::ExternalPropagator {
    CaDiCaL::Solver * solver;
    std::vector<std::vector<int>> new_clauses;
    std::deque<std::vector<int>> current_trail;
public:
    SymmetryBreaker(CaDiCaL::Solver * s, int order) : solver(s) {
        if (order == 0) {
            std::cout << "c Need to provide order to use programmatic symmetry breaking" << std::endl;
            return;
        }
        std::cout << "c Solving the first UNSAT pigeonhole problem of order " << order << std::endl;
        n = order;
        solver->connect_external_propagator(this);
        for (int h = 0; h < n; h++)
            for (int p = 0; p < n + 1; p++)
            solver->add_observed_var(ph(p,h));

        // The root-level of the trail is always there
        current_trail.push_back(std::vector<int>());
    }

    ~SymmetryBreaker () {
        solver->disconnect_external_propagator ();
    }

    void notify_assignment(int lit, bool is_fixed) {
        if (is_fixed) {
            current_trail.front().push_back(lit);
        } else {
            current_trail.back().push_back(lit);
        }

        int p = pigeon_id(lit);
        int h = hole_id(lit);
        int j = p + 1;
        assert(ph(p,h) == abs(lit));

        if (lit > 0) {
            if (p < 1 || p >= n - 1 || h < p + 1 || h >= n ) return;

            if (has_lit(current_trail,-ph(j-1,j))) {
#ifdef VERBOSE
                std::cout << "c THEORY-LOG Conflict-1 is found over binary clause: " << ph(j-1,j) << " || " << -ph(j-1,h) << std::endl;
#endif
                std::vector<int> clause;
                clause.push_back(ph(j-1,j));
                clause.push_back(-ph(j-1,h));
                new_clauses.push_back(clause);
                return;
            } else if (!has_lit(current_trail,ph(j-1,j))) {
#ifdef VERBOSE
                std::cout << "c THEORY-LOG Propagation-1 is found over binary clause: " << ph(j-1,j) << " || " << -ph(j-1,h) << std::endl;
#endif
                std::vector<int> clause;
                clause.push_back(ph(j-1,j));
                clause.push_back(-ph(j-1,h));
                new_clauses.push_back(clause);
            }
        } else {
            if (p + 1 != h || p < 1 || p >= n - 1) return;
            assert (-lit == ph(p, p+1)); // ph(j-1, j) is assigned false --> -ph (j-1, k) must be non-falsified for all k > j

            for (int k = j + 1; k < n; k++) {
                if (has_lit(current_trail,ph(j-1,k))) {
#ifdef VERBOSE
                    std::cout << "c THEORY-LOG Conflict-2 is found over binary clause: " << ph(j-1,j) << " || " << -ph(j-1,k) << std::endl;
#endif
                    std::vector<int> clause;
                    clause.push_back(ph(j-1,j));
                    clause.push_back(-ph(j-1,k));
                    new_clauses.push_back(clause);
                    return;
                } else if (!has_lit(current_trail,-ph(j-1,k))) {
#ifdef VERBOSE
                    std::cout << "c THEORY-LOG Propagation-2 is found over binary clause: " << ph(j-1,j) << " || " << -ph(j-1,k) << std::endl;
#endif
                    std::vector<int> clause;
                    clause.push_back(ph(j-1,j));
                    clause.push_back(-ph(j-1,k));
                    new_clauses.push_back(clause);
                }
            }
        }
    }

    void notify_new_decision_level () {
        current_trail.push_back(std::vector<int>());
    }

    void notify_backtrack (size_t new_level) {
        while (current_trail.size() > new_level + 1) {
            current_trail.pop_back();
        }
    }

    bool cb_check_found_model (const std::vector<int> & model) { 
        (void) model;
        return true;
    }

    bool cb_has_external_clause () {
#ifdef VERBOSE
        if (!new_clauses.empty()) {
            std::cout << "c New blocking clause: ";
            size_t clause_idx = new_clauses.size() - 1;
            for (const auto& lit: new_clauses[clause_idx]) {
                std::cout << lit << " ";
            }
            std::cout << " 0" << std::endl;
        }
#endif
        return (!new_clauses.empty());
    }

    int cb_add_external_clause_lit () {
        if (new_clauses.empty()) return 0;
        else {
            assert(!new_clauses.empty());
            size_t clause_idx = new_clauses.size() - 1;
            if (new_clauses[clause_idx].empty()) {
                new_clauses.pop_back();
                return 0;
            }

            int lit = new_clauses[clause_idx].back();
            new_clauses[clause_idx].pop_back();
            return lit;
        }
    }

    int cb_decide () { return 0; }
    int cb_propagate () { return 0; }
    int cb_add_reason_clause_lit (int plit) {
        (void)plit;
        return 0;
    };
};

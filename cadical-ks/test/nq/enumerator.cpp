#ifdef UNDEFVERBOSE
#undef VERBOSE
#endif

static int pos (int row, int col, int n) {
    assert (0 <= row), assert (row < n);
    assert (0 <= col), assert (col < n);
    return (n * row) + col + 1;
}

class SolutionEnumerator : CaDiCaL::ExternalPropagator {
    CaDiCaL::Solver * solver;
    std::vector<int> blocking_clause = {};
    size_t full_assignment_size = 0;
public:
    int sol_count = 0; //TODO check if the solutions are uniq

    SolutionEnumerator(CaDiCaL::Solver * s, int n) : solver(s) {
        if (n == 0) {
            std::cout << "c Need to provide order to use programmatic enumeration" << std::endl;
            return;
        }
        std::cout << "c Enumerating solutions of the " << n << "-Queens problem." << std::endl;
        solver->connect_external_propagator(this);
        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                solver->add_observed_var (pos (i, j, n));

        is_lazy = true;
        //is_lazy = false;
        full_assignment_size = solver->active ();
    }
    ~SolutionEnumerator () { solver->disconnect_external_propagator (); }

    void process_trail (const std::vector<int> & current_trail) {
        (void) current_trail;
        assert(!is_lazy || false); //if is_lazy is true, this function should never be called
        return;
    }

    bool cb_check_found_model (const std::vector<int> & model) {
        assert(model.size() == full_assignment_size);
        sol_count += 1;

        blocking_clause.clear();

#ifdef VERBOSE
        std::cout << "c New solution was found: ";
#endif
        for (const auto& lit: model) {
            if (lit > 0) {
#ifdef VERBOSE
                std::cout << lit << " ";
#endif
                blocking_clause.push_back(-lit);
            }
        }
#ifdef VERBOSE
        std::cout << std::endl;
#endif

        return false;
    }

    bool cb_has_external_clause () {
        return (!blocking_clause.empty());
    }

    int cb_add_external_clause_lit () {
        if (blocking_clause.empty()) return 0;
        else {
            int lit = blocking_clause.back();
            blocking_clause.pop_back();
            return lit;
        }
    }



    void notify_assignment (int,bool) {};
    void notify_new_decision_level () {};
    void notify_backtrack (size_t) {};
    int cb_decide () { return 0; }
    int cb_propagate () { return 0; }
    int cb_add_reason_clause_lit (int) { return 0; };
};

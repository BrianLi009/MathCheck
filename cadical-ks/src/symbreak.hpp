#include "internal.hpp"
#include <set>
#include "../../nauty2_8_8/nauty.h"
#include "../../nauty2_8_8/naugroup.h"

#define l_False 0
#define l_True 1
#define l_Undef 2

#define MAX(X,Y) ((X) > (Y)) ? (X) : (Y)
#define MIN(X,Y) ((X) > (Y)) ? (Y) : (X)

const int MAXORDER = 40;

class SymmetryBreaker : CaDiCaL::ExternalPropagator {
    CaDiCaL::Solver * solver;
    std::vector<std::vector<int>> new_clauses;
    std::deque<std::vector<int>> current_trail;
    int * assign;
    bool * fixed;
    int * colsuntouched;
    int n = 0;
    int unembeddable_check = 0;
    long sol_count = 0;
    int num_edge_vars = 0;
    std::set<unsigned long> canonical_hashes[MAXORDER];
    std::set<unsigned long> solution_hashes;

    // Add nauty-related members
    DEFAULTOPTIONS_GRAPH(options);
    statsblk stats;
    setword workspace[100];
    int lab[MAXORDER], ptn[MAXORDER], orbits[MAXORDER];
    graph g[MAXORDER*MAXORDER];

    int orbit_cutoff = 0;  // Default value of 0 means no cutoff
    bool pseudo_enabled = true;  // Default value is true

    // Add nauty statistics
    long nauty_calls = 0;
    double nauty_time = 0;

public:
    SymmetryBreaker(CaDiCaL::Solver * s, int order, int uc);
    ~SymmetryBreaker ();
    void notify_assignment(int lit, bool is_fixed);
    void notify_new_decision_level ();
    void notify_backtrack (size_t new_level);
    bool cb_check_found_model (const std::vector<int> & model);
    bool cb_has_external_clause ();
    int cb_add_external_clause_lit ();
    int cb_decide ();
    int cb_propagate ();
    int cb_add_reason_clause_lit (int plit);
    bool is_canonical(int k, int p[], int& x, int& y, int& i, bool opt_pseudo_test);
    bool has_mus_subgraph(int k, int* P, int* p, int g);
    std::vector<int> compute_and_print_orbits(int k);
    std::vector<char> convert_assignment_to_graph6(int k);
    
    void setOrbitCutoff(int cutoff) { orbit_cutoff = cutoff; }
    void setPseudoEnabled(bool enabled) { pseudo_enabled = enabled; }
    bool isPseudoEnabled() const { return pseudo_enabled; }

private:
    void remove_possibilities(int k, int pn[], const std::vector<int>& orbits);
};

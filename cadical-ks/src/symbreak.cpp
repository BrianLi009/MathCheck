#include "symbreak.hpp"
#include <iostream>
#include <algorithm>
#include "hash_values.h"
#include "../../nauty2_8_8/nauty.h"
#include <unordered_set>
#include <string>
#include <chrono>
#include <cstring>
#include <bitset>
#include <iomanip>
#include <vector>
#include <unordered_map>

FILE * canonicaloutfile = NULL;
FILE * noncanonicaloutfile = NULL;
FILE * exhaustfile = NULL;

// The kth entry estimates the number of permuations needed to show canonicity in order (k+1)
long perm_cutoff[MAXORDER] = {0, 0, 0, 0, 0, 0, 20, 50, 125, 313, 783, 1958, 4895, 12238, 30595, 76488, 191220, 478050, 1195125, 2987813, 7469533, 18673833, 46684583};
long canon = 0;
long noncanon = 0;
double canontime = 0;
double noncanontime = 0;
long canonarr[MAXORDER] = {};
long noncanonarr[MAXORDER] = {};
double canontimearr[MAXORDER] = {};
double noncanontimearr[MAXORDER] = {};
#ifdef PERM_STATS
long canon_np[MAXORDER] = {};
long noncanon_np[MAXORDER] = {};
#endif

// Add at the top with other global variables
long perms_tried_by_order[MAXORDER] = {};
bool lex_greatest = false;  // Default to lex-least checking

SymmetryBreaker::SymmetryBreaker(CaDiCaL::Solver * s, int order, int unembeddable_check) : solver(s) {
    if (order == 0) {
        std::cout << "c Need to provide order to use programmatic code" << std::endl;
        return;
    }
    
    // Initialize parameters from solver's settings
    lex_greatest = solver->lex_greatest;
    
    // Initialize everything first
    n = order;
    num_edge_vars = n*(n-1)/2;
    assign = new int[num_edge_vars];
    fixed = new bool[num_edge_vars];
    colsuntouched = new int[n];
    solver->connect_external_propagator(this);
    for (int i = 0; i < num_edge_vars; i++) {
        assign[i] = l_Undef;
        fixed[i] = false;
    }

    // Rest of initialization
    std::cout << "c Running orderly generation on order " << n << " (" << num_edge_vars << " edge variables)" << std::endl;
    // The root-level of the trail is always there
    current_trail.push_back(std::vector<int>());
    // Observe the edge variables for orderly generation
    for (int i = 0; i < num_edge_vars; i++) {
        solver->add_observed_var(i+1);
    }
    learned_clauses_count = 0;

    // Initialize nauty options
    options.getcanon = FALSE;
    options.digraph = FALSE;
    options.writeautoms = FALSE;
    options.writemarkers = FALSE;
    options.defaultptn = FALSE;
    options.cartesian = FALSE;
    options.linelength = 0;
    options.outfile = NULL;
    options.userrefproc = NULL;
    options.userautomproc = NULL;
    options.userlevelproc = NULL;
    options.usernodeproc = NULL;
    options.usercanonproc = NULL;

    // We'll print the parameter table in setOrbitCutoff instead
}

SymmetryBreaker::~SymmetryBreaker () {
    if (n != 0) {
        solver->disconnect_external_propagator ();
        delete [] assign;
        delete [] colsuntouched;
        delete [] fixed;
        printf("Number of solutions   : %ld\n", sol_count);
        printf("Canonical subgraphs   : %-12" PRIu64 "   (%.0f /sec)\n", (uint64_t)canon, canon/canontime);
        for(int i=2; i<n; i++) {
#ifdef PERM_STATS
            printf("          order %2d    : %-12" PRIu64 "   (%.0f /sec) %.0f avg. perms\n", i+1, (uint64_t)canonarr[i], canonarr[i]/canontimearr[i], canon_np[i]/(float)(canonarr[i] > 0 ? canonarr[i] : 1));
#else
            printf("          order %2d    : %-12" PRIu64 "   (%.0f /sec)\n", i+1, (uint64_t)canonarr[i], canonarr[i]/canontimearr[i]);
#endif
        }
        printf("Noncanonical subgraphs: %-12" PRIu64 "   (%.0f /sec)\n", (uint64_t)noncanon, noncanon/noncanontime);
        for(int i=2; i<n; i++) {
#ifdef PERM_STATS
            printf("          order %2d    : %-12" PRIu64 "   (%.0f /sec) %.0f avg. perms\n", i+1, (uint64_t)noncanonarr[i], noncanonarr[i]/noncanontimearr[i], noncanon_np[i]/(float)(noncanonarr[i] > 0 ? noncanonarr[i] : 1));
#else
            printf("          order %2d    : %-12" PRIu64 "   (%.0f /sec)\n", i+1, (uint64_t)noncanonarr[i], noncanonarr[i]/noncanontimearr[i]);
#endif
        }
        printf("Canonicity checking   : %g s\n", canontime);
        printf("Noncanonicity checking: %g s\n", noncanontime);
        printf("Total canonicity time : %g s\n", canontime+noncanontime);

        print_stats();
    }
}

void SymmetryBreaker::notify_assignment(int lit, bool is_fixed) {
    assign[abs(lit)-1] = (lit > 0 ? l_True : l_False);
    if (is_fixed) {
        fixed[abs(lit)-1] = true;
    } else {
        current_trail.back().push_back(lit);
    }
}

void SymmetryBreaker::notify_new_decision_level () {
    current_trail.push_back(std::vector<int>());
}

void SymmetryBreaker::notify_backtrack (size_t new_level) {
    while (current_trail.size() > new_level + 1) {
        for (const auto& lit: current_trail.back()) {
            const int x = abs(lit) - 1;
            // Don't remove literals that have been fixed
            if(fixed[x])
                continue;
            assign[x] = l_Undef;
            const int col = 1+(-1+sqrt(1+8*x))/2;
            for(int i=col; i<n; i++)
                colsuntouched[i] = false;
        }
        current_trail.pop_back();
    }
}

bool SymmetryBreaker::cb_check_found_model (const std::vector<int> & model) {
    assert(model.size() == num_edge_vars);
    sol_count += 1;

#ifdef VERBOSE
    std::cout << "c New solution was found: ";
#endif
    std::vector<int> clause;
    for (const auto& lit: model) {
#ifdef VERBOSE
        if (lit > 0) {
            std::cout << lit << " ";
        }
#endif
        clause.push_back(-lit);
    }
#ifdef VERBOSE
    std::cout << std::endl;
#endif
    new_clauses.push_back(clause);
    solver->add_trusted_clause(clause);

    // Print the adjacency matrix for the current model
    //print_adjacency_matrix();

    return false;
}

bool SymmetryBreaker::cb_has_external_clause () {
    if(!new_clauses.empty())
        return true;

    static int partial_assignment_count = 0;

    long hash = 0;

    // Initialize i to be the first column that has been touched since the last analysis
    int i = 2;
    for(; i < n; i++) {
        if(!colsuntouched[i])
            break;
    }
    // Ensure variables are defined and update current graph hash
    for(int j = 0; j < i*(i-1)/2; j++) {
        if(assign[j] == l_Undef)
            return false;
        else if(assign[j] == l_True)
            hash += hash_values[j];
    }
    for(; i < n; i++) {
        // Ensure variables are defined and update current graph hash
        for(int j = i*(i-1)/2; j < i*(i+1)/2; j++) {
            if(assign[j]==l_Undef) {
                return false;
            }
            if(assign[j]==l_True) {
                hash += hash_values[j];
            }
        }
        colsuntouched[i] = true;

        // Check if it's a full assignment or if it's time to perform a canonicity check
        if (i == n - 1 || partial_assignment_count % 1 == 0) {
            // Check if current graph hash has been seen
            if(canonical_hashes[i].find(hash)==canonical_hashes[i].end())
            {
                // Compute and print orbits only when we need to check canonicity
                //compute_and_print_orbits(i + 1);

                // Found a new subgraph of order i+1 to test for canonicity
                // Uses a pseudo-check except when i+1 = n
                const double before = CaDiCaL::absolute_process_time();
                // Run canonicity check
                int p[i+1]; // Permutation on i+1 vertices
                int x, y;   // These will be the indices of first adjacency matrix entry that demonstrates noncanonicity (when such indices exist)
                int mi;     // This will be the index of the maximum defined entry of p
                bool ret = (hash == 0) ? true : is_canonical(i+1, p, x, y, mi, i < n-1);
#ifdef VVERBOSE
                if(!ret) {
                    printf("x: %d y: %d, mi: %d, ", x, y, mi);
                    printf("p^(-1)(x): %d, p^(-1)(y): %d | ", p[x], p[y]);
                    for(int j=0; j<i+1; j++) {
                        if(j != p[j]) {
                            printf("%d ", p[j]);
                        } else printf("* ");
                    }
                    printf("\n");
                }
#endif
                const double after = CaDiCaL::absolute_process_time();

                // If subgraph is canonical
                if (ret) {
                    canon++;
                    canontime += (after-before);
                    canonarr[i]++;
                    canontimearr[i] += (after-before);
                    canonical_hashes[i].insert(hash);

                    //std::cout << "Partial assignment of size " << i+1 << " is canonical" << std::endl;

                    if(canonicaloutfile != NULL) {
                        fprintf(canonicaloutfile, "a ");
                        for(int j = 0; j < i*(i+1)/2; j++)
                            fprintf(canonicaloutfile, "%s%d ", assign[j]==l_True ? "" : "-", j+1);
                        fprintf(canonicaloutfile, "0\n");
                        fflush(canonicaloutfile);
                    }
#ifdef VVERBOSE
                    int count = 0;
                    int A[n][n] = {};
                    for(int jj=0; jj<n; jj++) {
                        for(int ii=0; ii<jj; ii++) {
                            if(assign[count]==l_True) {
                                A[ii][jj] = 1;
                                A[jj][ii] = 1;
                            }
                            if(assign[count]==l_False) {
                                A[ii][jj] = -1;
                                A[jj][ii] = -1;
                            }
                            count++;
                        }
                    }
                    for(int ii=0; ii<n; ii++) {
                        for(int jj=0; jj<n; jj++) {
                            printf("%c", A[ii][jj] == 0 ? '?' : A[ii][jj] == -1 ? '0' : '1');
                        }
                        printf("\n");
                    }
                    printf("\n");
                    printf("a ");
                    for (int i = 0; i<n*(n-1)/2; i++) {
                        printf("%s%d ", assign[i] == l_True ? "" : "-", i+1);
                    }
                    printf("\n");
#endif
                }
                // If subgraph is not canonical then block it
                else {
                    noncanon++;
                    noncanontime += (after-before);
                    noncanonarr[i]++;
                    noncanontimearr[i] += (after-before);
                    new_clauses.push_back(std::vector<int>());

                    //std::cout << "Partial assignment of size " << i+1 << " is not canonical" << std::endl;

                    // Generate a blocking clause smaller than the naive blocking clause
                    new_clauses.back().push_back(-(x*(x-1)/2+y+1));
                    const int px = MAX(p[x], p[y]);
                    const int py = MIN(p[x], p[y]);
                    new_clauses.back().push_back(px*(px-1)/2+py+1);
                    for(int ii=0; ii < x+1; ii++) {
                        for(int jj=0; jj < ii; jj++) {
                            if(ii==x && jj==y) {
                                break;
                            }
                            const int pii = MAX(p[ii], p[jj]);
                            const int pjj = MIN(p[ii], p[jj]);
                            if(ii==pii && jj==pjj) {
                                continue;
                            } else if(assign[ii*(ii-1)/2+jj] == l_True) {
                                new_clauses.back().push_back(-(ii*(ii-1)/2+jj+1));
                            } else if (assign[pii*(pii-1)/2+pjj] == l_False) {
                                new_clauses.back().push_back(pii*(pii-1)/2+pjj+1);
                            }
                        }
                    }
                    // To generate the naive blocking clause:
                    /*for(int j = 0; j < i*(i+1)/2; j++)
                        new_clauses.back().push_back((j+1) * assign[j]==l_True ? -1 : 1);*/

                    solver->add_trusted_clause(new_clauses.back());
                    learned_clauses_count++;

                    if(noncanonicaloutfile != NULL) {
                        //fprintf(noncanonicaloutfile, "a ");
                        const int size = new_clauses.back().size();
                        for(int j = 0; j < size; j++)
                            fprintf(noncanonicaloutfile, "%d ", new_clauses.back()[j]);
                        fprintf(noncanonicaloutfile, "0\n");
                        fflush(noncanonicaloutfile);
                    }

                    if(solver->permoutfile != NULL) {
                        for(int j = 0; j <= mi; j++)
                            fprintf(solver->permoutfile, "%s%d", j == 0 ? "" : " ", p[j]);
                        fprintf(solver->permoutfile, "\n");
                    }

                    return true;
                }
            }
        }

        // Increment the partial assignment count
        partial_assignment_count++;
    }

    // No programmatic clause generated
    return false;
}

int SymmetryBreaker::cb_add_external_clause_lit () {
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

int SymmetryBreaker::cb_decide () { return 0; }
int SymmetryBreaker::cb_propagate () { return 0; }
int SymmetryBreaker::cb_add_reason_clause_lit (int plit) {
    (void)plit;
    return 0;
};

// Returns true when the k-vertex subgraph (with adjacency matrix M) is canonical
// M is determined by the current assignment to the first k*(k-1)/2 variables
// If M is noncanonical, then p, x, and y will be updated so that
// * p will be a permutation of the rows of M so that row[i] -> row[p[i]] generates a matrix smaller than M (and therefore demonstrates the noncanonicity of M)
// * (x,y) will be the indices of the first entry in the permutation of M demonstrating that the matrix is indeed lex-smaller than M
// * i will be the maximum defined index defined in p
bool SymmetryBreaker::is_canonical(int k, int p[], int& x, int& y, int& i, bool opt_pseudo_test) {
    int pl[k]; // pl[k] contains the current list of possibilities for kth vertex (encoded bitwise)
    int pn[k+1]; // pn[k] contains the initial list of possibilities for kth vertex (encoded bitwise)
    
    // Initialize all possibilities
    for (int j = 0; j <= k; j++) {
        pn[j] = (1 << k) - 1;
    }

    // Only compute orbits and remove possibilities if k is greater than orbit_cutoff
    if (k > orbit_cutoff) {
        // Compute orbits
        std::vector<int> orbits = compute_and_print_orbits(k);
        // Remove possibilities before starting
        remove_possibilities(k, pn, orbits);
    }

    for (int j = 0; j <= k; j++) {
        pl[j] = pn[j];
    }
    i = 0;
    int last_x = 0;
    int last_y = 0;

    int np = 1;
    int limit = INT32_MAX;

    // If pseudo-test enabled then stop test if it is taking over 10 times longer than average
    if(pseudo_enabled && opt_pseudo_test && k >= 7) {
        limit = 10*perm_cutoff[k-1];
    }

    while(np < limit) {
        perms_tried_by_order[k-1]++;  // Increment counter for this order
        
        // If no possibilities for ith vertex then backtrack
        while (pl[i] == 0) {
            i--;
            if (i == -1) {
#ifdef PERM_STATS
                canon_np[k-1] += np;
#endif
                return true;
            }
            // Reset possibilities for the next vertex
            pl[i+1] = pn[i+1];
            
            // Reset last_x and last_y when backtracking
            last_x = 0;
            last_y = 0;
        }

        p[i] = __builtin_ctz(pl[i]); // Get index of rightmost high bit
        pl[i] &= pl[i] - 1;  // Remove this possibility
        
        if (i < k - 1) {
            pl[i+1] = pn[i+1] & ~(1 << p[i]); // Update possibilities for next vertex
        }

        // If pseudo-test enabled then stop shortly after the first row is no longer fixed
        if(i == 0 && p[i] == 1 && opt_pseudo_test && k < n) {
            limit = np + 100;
        }

        // Always start the lex comparison from the beginning for each new permutation
        last_x = 0;
        last_y = 0;

        // Determine if the permuted matrix p(M) is lex-smaller/greater than M
        bool lex_result_unknown = false;
        x = 1;
        y = 0;
        int j;
        for(j = 0; j < k*(k-1)/2; j++) {
            if(x > i) {
                lex_result_unknown = true;
                break;
            }
            const int px = MAX(p[x], p[y]);
            const int py = MIN(p[x], p[y]);
            const int pj = px*(px-1)/2 + py;
            if(assign[j] != assign[pj]) {
                if((!lex_greatest && assign[j] == l_False && assign[pj] == l_True) ||
                   (lex_greatest && assign[j] == l_True && assign[pj] == l_False)) {
                    // P(M) > M for lex-least or P(M) < M for lex-greatest
                    total_larger_perms++;
                    break;
                }
                if((!lex_greatest && assign[j] == l_True && assign[pj] == l_False) ||
                   (lex_greatest && assign[j] == l_False && assign[pj] == l_True)) {
                    // P(M) < M for lex-least or P(M) > M for lex-greatest
                    total_smaller_perms++;
                    generate_blocking_clause_smaller(k, p, x, y);
                    return false;
                }
            }

            y++;
            if(x==y) {
                x++;
                y = 0;
            }
        }
        last_x = x;
        last_y = y;

        if(lex_result_unknown) {
            i++;
            if (i < k) {
                pl[i] = pn[i];
                for (int j = 0; j < i; j++) {
                    pl[i] &= ~(1 << p[j]);  // Remove already used vertices
                }
            }
        }
        else {
            np++;
        }
    }

    // Pseudo-test return: Assume matrix is canonical if a noncanonical permutation witness not yet found
#ifdef PERM_STATS
    canon_np[k-1] += np;
#endif
    return true;
}

void SymmetryBreaker::generate_blocking_clause_smaller(int k, int p[], int x, int y) {
    auto start = std::chrono::high_resolution_clock::now();
    smaller_calls++;

    std::vector<int> clause;
    clause.reserve(3);
    
    // Adjust the clause generation based on lex_greatest
    if (!lex_greatest) {
        clause.push_back(-(x*(x-1)/2+y+1));
        clause.push_back(p[x]*(p[x]-1)/2+p[y]+1);
    } else {
        clause.push_back(x*(x-1)/2+y+1);
        clause.push_back(-(p[x]*(p[x]-1)/2+p[y]+1));
    }
    
    for(int ii=0; ii < x+1; ii++) {
        for(int jj=0; jj < ii; jj++) {
            if(ii==x && jj==y) {
                break;
            }
            const int pii = MAX(p[ii], p[jj]);
            const int pjj = MIN(p[ii], p[jj]);
            if(ii==pii && jj==pjj) {
                continue;
            } else if((!lex_greatest && assign[ii*(ii-1)/2+jj] == l_True) ||
                     (lex_greatest && assign[ii*(ii-1)/2+jj] == l_False)) {
                clause.push_back(-(ii*(ii-1)/2+jj+1));
                goto add_clause;
            } else if((!lex_greatest && assign[pii*(pii-1)/2+pjj] == l_False) ||
                     (lex_greatest && assign[pii*(pii-1)/2+pjj] == l_True)) {
                clause.push_back(pii*(pii-1)/2+pjj+1);
                goto add_clause;
            }
        }
    }

add_clause:
    // Sort the clause to ensure consistent representation
    std::sort(clause.begin(), clause.end());

    // Create a string representation of the clause
    std::string clause_str = std::to_string(clause[0]);
    for (size_t i = 1; i < clause.size(); ++i) {
        clause_str += ' ' + std::to_string(clause[i]);
    }

    // Check if this clause has already been generated
    if (generated_clauses.insert(clause_str).second) {
        // If it's a new clause, add it to the solver
        solver->add_trusted_clause(clause);
        learned_clauses_count++;
        smaller_clauses_generated++;  // Increment the counter for actually generated clauses
    }

    auto end = std::chrono::high_resolution_clock::now();
    smaller_time += std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
}

void SymmetryBreaker::print_adjacency_matrix() {
    int count = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (i == j) {
                std::cout << '0';
            } else if (j > i) {
                std::cout << (assign[count] == l_True ? '1' : (assign[count] == l_False ? '0' : '?'));
                count++;
            } else {
                std::cout << (assign[i*(i-1)/2 + j] == l_True ? '1' : (assign[i*(i-1)/2 + j] == l_False ? '0' : '?'));
            }
        }
        std::cout << std::endl;
    }
    std::cout << std::endl;
}

void SymmetryBreaker::print_matrix(int k, const int p[]) {
    int p_copy[MAXORDER];
    for (int i = 0; i < k; i++) {
        p_copy[i] = p[i];
    }
    for (int i = 0; i < k; i++) {
        for (int j = 0; j < k; j++) {
            if (i == j) {
                std::cout << '0';
            } else {
                int x = MAX(p_copy[i], p_copy[j]);
                int y = MIN(p_copy[i], p_copy[j]);
                int idx = x * (x - 1) / 2 + y;
                std::cout << (assign[idx] == l_True ? '1' : (assign[idx] == l_False ? '0' : '?'));
            }
        }
        std::cout << std::endl;
    }
    std::cout << std::endl;
}

void SymmetryBreaker::print_stats() {
    std::cout << "Total permutations P satisfying P(M) > M: " << total_larger_perms << std::endl;
    std::cout << "Total permutations P satisfying P(M) < M: " << total_smaller_perms << std::endl;
    std::cout << "Total permutations tried by order:" << std::endl;
    for(int i = 0; i < n; i++) {
        if(perms_tried_by_order[i] > 0) {
            std::cout << "  Order " << i+1 << ": " << perms_tried_by_order[i] << std::endl;
        }
    }
    std::cout << "generate_blocking_clause_smaller: " << smaller_calls << " calls, " 
              << smaller_time << " microseconds total, " 
              << (smaller_calls > 0 ? smaller_time / smaller_calls : 0) << " microseconds average per call\n";
    
    // Add nauty statistics
    std::cout << "Nauty statistics:" << std::endl;
    std::cout << "  Total calls to nauty: " << nauty_calls << std::endl;
    std::cout << "  Total time in nauty: " << nauty_time << " seconds" << std::endl;
    if (nauty_calls > 0) {
        std::cout << "  Average time per nauty call: " << (nauty_time / nauty_calls) * 1000 << " milliseconds" << std::endl;
    }
}

void SymmetryBreaker::print_permutation(int k, const int p[]) {
    std::cout << "Permutation: ";
    for (int i = 0; i < k; i++) {
        std::cout << p[i] << " ";
    }
    std::cout << std::endl;
}

int SymmetryBreaker::get_unit_clause_literal(int k, int p[], int x, int y) {
    (void)x; (void)y; // Parameters are intentionally unused
    for (int i = 0; i < k; i++) {
        for (int j = 0; j < i; j++) {
            if (assign[i*(i-1)/2 + j] != assign[p[i]*(p[i]-1)/2 + p[j]]) {
                if (assign[i*(i-1)/2 + j] == l_False) {
                    return i*(i-1)/2 + j + 1;
                } else {
                    return -(i*(i-1)/2 + j + 1);
                }
            }
        }
    }
    return 0;  // No unit clause found
}

std::vector<int> SymmetryBreaker::compute_and_print_orbits(int k) {
    auto start = std::chrono::high_resolution_clock::now();
    nauty_calls++;  // Increment counter

    std::vector<char> g6 = convert_assignment_to_graph6(k);
    if (g6.empty()) return std::vector<int>();

    int n = k;
    int m = SETWORDSNEEDED(n);
    nauty_check(WORDSIZE, m, n, NAUTYVERSIONID);

    std::vector<graph> g(m * n);
    EMPTYGRAPH(g.data(), m, n);

    int pos = 0;
    for (int j = 1; j < n; ++j) {
        for (int i = 0; i < j; ++i) {
            if (g6[pos] == '1') {
                ADDONEEDGE(g.data(), i, j, m);
            }
            ++pos;
        }
    }

    std::vector<int> orbits(n);
    for (int i = 0; i < n; ++i) {
        lab[i] = i;
        ptn[i] = 1;
    }
    ptn[n-1] = 0;

    densenauty(g.data(), lab, ptn, orbits.data(), &options, &stats, m, n, NULL);

    auto end = std::chrono::high_resolution_clock::now();
    nauty_time += std::chrono::duration<double>(end - start).count();

    return orbits;
}

std::vector<char> SymmetryBreaker::convert_assignment_to_graph6(int k) {
    std::vector<char> g6;
    g6.reserve(k * (k - 1) / 2);

    for (int j = 1; j < k; ++j) {
        for (int i = 0; i < j; ++i) {
            g6.push_back((assign[j*(j-1)/2 + i] == l_True) ? '1' : '0');
        }
    }

    return g6;
}


void SymmetryBreaker::remove_possibilities(int k, int pn[], const std::vector<int>& orbits) {
    if (k <= 2) return; // Early exit for small graphs where pruning has minimal impact
    
    // Pre-compute orbit statistics to determine if pruning is worthwhile
    int orbit_count = 0;
    for (int i = 0; i < k; i++) {
        orbit_count = std::max(orbit_count, orbits[i] + 1);
    }
    if (orbit_count == k) return; // No non-trivial orbits
    
    // Current implementation is good but could be optimized by:
    // 1. Using bitset operations more extensively
    // 2. Pre-computing orbit masks at initialization
    // 3. Adding early exit conditions when no pruning is possible
    
    if (k <= 0 || k > MAXORDER || orbits.size() != static_cast<size_t>(k)) {
        return;
    }

    // Step 1: Create orbit masks for efficient operations
    std::vector<int> orbit_masks(k, 0);
    std::vector<int> orbit_mins(k, k);
    
    // Build orbit masks and find minimum vertices in one pass
    for (int i = 0; i < k; i++) {
        int orbit_id = orbits[i];
        orbit_masks[orbit_id] |= (1 << i);
        orbit_mins[orbit_id] = std::min(orbit_mins[orbit_id], i);
    }

    // Step 2: Apply restrictions based on orbit structure
    for (int i = 0; i < k; i++) {
        int orbit_id = orbits[i];
        int min_vertex = orbit_mins[orbit_id];
        
        // Only restrict mappings for non-minimal vertices in their orbit
        if (i > min_vertex) {
            // Can't map to vertices lower than the orbit's minimum
            int forbidden_mask = (1 << min_vertex) - 1;  // All bits < min_vertex
            // Also can't map to vertices in same orbit that are lower than current vertex
            forbidden_mask |= ((1 << i) - 1) & orbit_masks[orbit_id];
            
            pn[i] &= ~forbidden_mask;  // Remove forbidden mappings
        }
    }
}

void SymmetryBreaker::setOrbitCutoff(int cutoff) {
    orbit_cutoff = cutoff;
    
    // Now print the parameter table after orbit_cutoff is set
    std::cout << "\nc Parameter Table:" << std::endl;
    std::cout << "c +-----------------+-------------+" << std::endl;
    std::cout << "c | Parameter       | Value       |" << std::endl;
    std::cout << "c +-----------------+-------------+" << std::endl;
    std::cout << "c | Order           | " << std::setw(11) << n << " |" << std::endl;
    std::cout << "c | Orbit cutoff    | " << std::setw(11) << orbit_cutoff << " |" << std::endl;
    std::cout << "c | Pseudo check    | " << std::setw(11) << (solver->pseudocheck ? "enabled" : "disabled") << " |" << std::endl;
    std::cout << "c | Lex mode        | " << std::setw(11) << (lex_greatest ? "greatest" : "least") << " |" << std::endl;
    std::cout << "c | Edge variables  | " << std::setw(11) << (n*(n-1)/2) << " |" << std::endl;
    std::cout << "c +-----------------+-------------+" << std::endl;
    std::cout << std::endl;
}

#include "symbreak.hpp"
#include <iostream>
#include "unembeddable_graphs.h"
#include "hash_values.h"

FILE * canonicaloutfile = NULL;
FILE * noncanonicaloutfile = NULL;
FILE * exhaustfile = NULL;
FILE * musoutfile = NULL;

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
long muscount = 0;
long muscounts[17] = {};
double mustime = 0;

SymmetryBreaker::SymmetryBreaker(CaDiCaL::Solver * s, int order, int uc) : solver(s) {
    if (order == 0) {
        std::cout << "c Need to provide order to use programmatic code" << std::endl;
        return;
    }
    if (uc == 0) {
        std::cout << "c Not checking for unembeddable subgraphs" << std::endl;
    } else {
        std::cout << "c Checking for " << uc << " unembeddable subgraphs" << std::endl;
    }
    n = order;
    num_edge_vars = n*(n-1)/2;
    unembeddable_check = uc;
    assign = new int[num_edge_vars];
    fixed = new bool[num_edge_vars];
    colsuntouched = new int[n];
    solver->connect_external_propagator(this);
    for (int i = 0; i < num_edge_vars; i++) {
        assign[i] = l_Undef;
        fixed[i] = false;
    }
    std::cout << "c Running orderly generation on order " << n << " (" << num_edge_vars << " edge variables)" << std::endl;
    // The root-level of the trail is always there
    current_trail.push_back(std::vector<int>());
    // Observe the edge variables for orderly generation
    for (int i = 0; i < num_edge_vars; i++) {
        solver->add_observed_var(i+1);
    }
}

SymmetryBreaker::~SymmetryBreaker () {
    if (n != 0) {
        solver->disconnect_external_propagator ();
        delete [] assign;
        delete [] colsuntouched;
        delete [] fixed;
        printf("Number of solutions   : %ld\n", sol_count);
        printf("Canonical subgraphs   : %-12" PRIu64 "   (%.0f /sec)\n", canon, canon/canontime);
        for(int i=2; i<n; i++) {
#ifdef PERM_STATS
            printf("          order %2d    : %-12" PRIu64 "   (%.0f /sec) %.0f avg. perms\n", i+1, canonarr[i], canonarr[i]/canontimearr[i], canon_np[i]/(float)(canonarr[i] > 0 ? canonarr[i] : 1));
#else
            printf("          order %2d    : %-12" PRIu64 "   (%.0f /sec)\n", i+1, canonarr[i], canonarr[i]/canontimearr[i]);
#endif
        }
        printf("Noncanonical subgraphs: %-12" PRIu64 "   (%.0f /sec)\n", noncanon, noncanon/noncanontime);
        for(int i=2; i<n; i++) {
#ifdef PERM_STATS
            printf("          order %2d    : %-12" PRIu64 "   (%.0f /sec) %.0f avg. perms\n", i+1, noncanonarr[i], noncanonarr[i]/noncanontimearr[i], noncanon_np[i]/(float)(noncanonarr[i] > 0 ? noncanonarr[i] : 1));
#else
            printf("          order %2d    : %-12" PRIu64 "   (%.0f /sec)\n", i+1, noncanonarr[i], noncanonarr[i]/noncanontimearr[i]);
#endif
        }
        printf("Canonicity checking   : %g s\n", canontime);
        printf("Noncanonicity checking: %g s\n", noncanontime);
        printf("Total canonicity time : %g s\n", canontime+noncanontime);
        if (unembeddable_check > 0) {
            printf("Unembeddable checking : %g s\n", mustime);
            for(int g=0; g<unembeddable_check; g++) {
                printf("        graph #%2d     : %-12" PRIu64 "\n", g, muscounts[g]);
            }
            printf("Total unembed. graphs : %ld\n", muscount);
        }
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

    return false;
}

bool SymmetryBreaker::cb_has_external_clause () {
    if(!new_clauses.empty())
        return true;

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

        // Check if current graph hash has been seen
        if(canonical_hashes[i].find(hash)==canonical_hashes[i].end())
        {
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

    for(int g=0; g<unembeddable_check; g++)
    {
        int p[12]; // If an umembeddable subgraph is found, p will contain which rows of M correspond with the rows of the lex greatest representation of the unembeddable subgraph
        int P[n];
        for(int j=0; j<n; j++) P[j] = -1;

        const double before = CaDiCaL::absolute_process_time();
        bool ret = has_mus_subgraph(n, P, p, g);
        const double after = CaDiCaL::absolute_process_time();
        mustime += (after-before);

        // If graph has minimal unembeddable subgraph (MUS)
        if (ret) {
            muscount++;
            muscounts[g]++;
            new_clauses.push_back(std::vector<int>());

#ifdef VERBOSE
            std::cout << "c Found minimal umbeddable subgraph #" << g << ": ";
#endif

            int c = 0;
            for(int jj=0; jj<n; jj++) {
                for(int ii=0; ii<jj; ii++) {
                    if(assign[c]==l_True && P[jj] != -1 && P[ii] != -1)
                        if((P[ii] < P[jj] && mus[g][P[ii] + P[jj]*(P[jj]-1)/2]) || (P[jj] < P[ii] && mus[g][P[jj] + P[ii]*(P[ii]-1)/2])) {
                            new_clauses.back().push_back(-(c+1));
#ifdef VERBOSE
                            std::cout << c+1 << " ";
#endif
                        }
                    c++;
                }
            }

#ifdef VERBOSE
            std::cout << std::endl;
#endif
            solver->add_trusted_clause(new_clauses.back());

            if(musoutfile != NULL) {
                //fprintf(musoutfile, "a ");
                int c = 0;
                for(int jj=0; jj<n; jj++) {
                    for(int ii=0; ii<jj; ii++) {
                        if(assign[c]==l_True && P[jj] != -1 && P[ii] != -1)
                            if((P[ii] < P[jj] && mus[g][P[ii] + P[jj]*(P[jj]-1)/2]) || (P[jj] < P[ii] && mus[g][P[jj] + P[ii]*(P[ii]-1)/2]))
                                fprintf(musoutfile, "-%d ", c+1);
                        c++;
                    }
                }

                fprintf(musoutfile, "0\n");
                fflush(musoutfile);
            }

            if(solver->permoutfile != NULL) {
                fprintf(solver->permoutfile, "Minimal unembeddable subgraph %d:", g);
                int mii = 10;
                if(g >= 2 && g < 7)
                    mii = 11;
                else if(g >= 7)
                    mii = 12;
                for(int ii=0; ii<mii; ii++) {
                    fprintf(solver->permoutfile, "%s%d", ii == 0 ? "" : " ", p[ii]);
                }
                fprintf(solver->permoutfile, "\n");
            }
            return true;
        }
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
    pl[0] = (1 << k) - 1;
    pn[0] = (1 << k) - 1;
    i = 0;
    int last_x = 0;
    int last_y = 0;

    int np = 1;
    int limit = INT32_MAX;

    // If pseudo-test enabled then stop test if it is taking over 10 times longer than average
    if(opt_pseudo_test && k >= 7) {
        limit = 10*perm_cutoff[k-1];
    }

    while(np < limit) {
        // If no possibilities for ith vertex then backtrack
        if(pl[i]==0) {
            // Backtrack to vertex that has at least two possibilities
            while((pl[i] & (pl[i] - 1)) == 0) {
                if(last_x > p[i]) {
                    last_x = p[i];
                    last_y = 0;
                }
                i--;
                if(i==-1) {
#ifdef PERM_STATS
                    canon_np[k-1] += np;
#endif
                    // No permutations produce a smaller matrix; M is canonical
                    return true;
                }
            }
            // Remove p[i] as a possibility from the ith vertex
            pl[i] = pl[i] & ~(1 << p[i]);
        }

        p[i] = log2(pl[i] & -pl[i]); // Get index of rightmost high bit
        pn[i+1] = pn[i] & ~(1 << p[i]); // List of possibilities for (i+1)th vertex

        // If pseudo-test enabled then stop shortly after the first row is no longer fixed
        if(i == 0 && p[i] == 1 && opt_pseudo_test && k < n) {
            limit = np + 100;
        }

        // Check if the entry on which to begin lex-checking needs to be updated
        if(last_x > p[i]) {
            last_x = p[i];
            last_y = 0;
        }
        if(i == last_x) {
            last_y = 0;
        }

        // Determine if the permuted matrix p(M) is lex-smaller than M
        bool lex_result_unknown = false;
        x = last_x == 0 ? 1 : last_x;
        y = last_y;
        int j;
        for(j=last_x*(last_x-1)/2+last_y; j<k*(k-1)/2; j++) {
            if(x > i) {
                // Unknown if permutation produces a larger or smaller matrix
                lex_result_unknown = true;
                break;
            }
            const int px = MAX(p[x], p[y]);
            const int py = MIN(p[x], p[y]);
            const int pj = px*(px-1)/2 + py;
            if(assign[j] == l_False && assign[pj] == l_True) {
                // Permutation produces a larger matrix; stop considering
                break;
            }
            if(assign[j] == l_True && assign[pj] == l_False) {
#ifdef PERM_STATS
                noncanon_np[k-1] += np;
#endif
                // Permutation produces a smaller matrix; M is not canonical
                return false;
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
            // Lex result is unknown; need to define p[i] for another i
            i++;
            pl[i] = pn[i];
        }
        else {
            np++;
            // Remove p[i] as a possibility from the ith vertex
            pl[i] = pl[i] & ~(1 << p[i]);
        }
    }

    // Pseudo-test return: Assume matrix is canonical if a noncanonical permutation witness not yet found
#ifdef PERM_STATS
    canon_np[k-1] += np;
#endif
    return true;
}

// Returns true when the k-vertex subgraph (with adjacency matrix M) contains the g-th minimal unembeddable graph
// M is determined by the current assignment to the first k*(k-1)/2 variables
// If an unembeddable subgraph is found in M, P is set to the mapping from the rows of M to the rows of the lex
// greatest representation of the unembeddable adjacency matrix (and p is the inverse of P)
bool SymmetryBreaker::has_mus_subgraph(int k, int* P, int* p, int g) {
    int pl[12]; // pl[k] contains the current list of possibilities for kth vertex (encoded bitwise)
    int pn[13]; // pn[k] contains the initial list of possibilities for kth vertex (encoded bitwise)
    pl[0] = (1 << k) - 1;
    pn[0] = (1 << k) - 1;
    int i = 0;

    while(1) {
        // If no possibilities for ith vertex then backtrack
        if(pl[i]==0) {
            // Backtrack to vertex that has at least two possibilities
            while((pl[i] & (pl[i] - 1)) == 0) {
                i--;
                if(i==-1) {
                    // No permutations produce a matrix containing the gth submatrix
                    return false;
                }
            }
            // Remove p[i] as a possibility from the ith vertex
            pl[i] = pl[i] & ~(1 << p[i]);
        }

        p[i] = log2(pl[i] & -pl[i]); // Get index of rightmost high bit
        pn[i+1] = pn[i] & ~(1 << p[i]); // List of possibilities for (i+1)th vertex

        // Determine if the permuted matrix p(M) is contains the gth submatrix
        bool result_known = false;
        for(int j=0; j<i; j++) {
            if(!mus[g][i*(i-1)/2+j])
                continue;
            const int px = MAX(p[i], p[j]);
            const int py = MIN(p[i], p[j]);
            const int pj = px*(px-1)/2 + py;
            if(assign[pj] == l_False) {
                // Permutation sends a non-edge to a gth submatrix edge; stop considering
                result_known = true;
                break;
            }
        }

        if(!result_known && ((i == 9 && g < 2) || (i == 10 && g < 7) || i == 11)) {
            // The complete gth submatrix found in p(M)
            for(int j=0; j<=i; j++) {
                P[p[j]] = j;
            }
            return true;
        }
        if(!result_known) {
            // Result is unknown; need to define p[i] for another i
            i++;
            pl[i] = pn[i];
        }
        else {
            // Remove p[i] as a possibility from the ith vertex
            pl[i] = pl[i] & ~(1 << p[i]);
        }
    }
}

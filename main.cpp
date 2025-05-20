#include <gtkmm.h>
#include <iostream>
#include <sstream>
#include <cstdio>
#include <array>
#include <fstream>
#include <chrono>
#include <iomanip>
#include <ctime>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <fcntl.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

class AppWindow : public Gtk::Window {
public:
    AppWindow() : m_is_running(false) {
        set_title("Gene Structure Pipeline");
        set_default_size(1000, 700);
        set_position(Gtk::WIN_POS_CENTER);

        // Script names
        script_buttons = {
            {"1_EXT_SPECIES.py", "1. EXT Species (Python)"},
            {"2_GENOMES_DOWNLOAD.py", "2. Genomes Download (Python)"},
            {"3_GENOMES_UNZIP.sh", "3. Genomes Unzip (Bash)"},
            {"4_GENOMES_MOVE.sh", "4. Genomes Move (Bash)"},
            {"5a_GENOMES_MAKEDB_INDIVIDUAL.sh", "5a. MakeDB Individual (Bash)"},
            {"5b_GENOMES_MAKEDB_MODEL.sh", "5b. MakeDB Manual (Bash)"},
            {"6_SEQUENCES_SPLIT.sh", "6. Sequences Split (Bash)"},
            {"7_SEQUENCES_TBLASTN.sh", "7. TBLASTN (Bash)"},
            {"8_AUGUSTUS.py", "8. AUGUSTUS (Python)"},
            {"9_EXONERATE.py", "9. EXONERATE (Python)"},
            {"10_SCHEMA.py", "10. Chromosome Schema (Python)"}
        };

        // Main Pannel
        main_paned.set_position(400);
        add(main_paned);

        // Left Pannel (Instructions)
        left_scroll.set_policy(Gtk::POLICY_AUTOMATIC, Gtk::POLICY_AUTOMATIC);
        left_scroll.add(left_vbox);
        main_paned.add1(left_scroll);

        // Right Pannel (Output)
        right_scroll.set_policy(Gtk::POLICY_AUTOMATIC, Gtk::POLICY_AUTOMATIC);
        right_scroll.add(output_view);
        output_view.set_editable(false);
        output_view.set_wrap_mode(Gtk::WRAP_WORD_CHAR);
        main_paned.add2(right_scroll);

        // Containers
        left_vbox.set_spacing(10);
        left_vbox.set_margin_top(10);
        left_vbox.set_margin_bottom(10);
        left_vbox.set_margin_left(10);
        left_vbox.set_margin_right(10);

        // Instructions Header
        auto* instructions_label = Gtk::make_managed<Gtk::Label>("INSTRUCTIONS");
        Pango::FontDescription font;
        font.set_weight(Pango::WEIGHT_BOLD);
        font.set_size(16 * PANGO_SCALE);
        instructions_label->override_font(font);
        instructions_label->set_halign(Gtk::ALIGN_CENTER);
        left_vbox.pack_start(*instructions_label, Gtk::PACK_SHRINK);
        
        auto* separator = Gtk::make_managed<Gtk::Separator>(Gtk::ORIENTATION_HORIZONTAL);
        left_vbox.pack_start(*separator, Gtk::PACK_SHRINK);
        
        // Instructions
        std::vector<std::string> steps = {
            "(EXT Species) Generate list of species from PROT_IDS.* (xlsx, tsv, csv) file (Insert in inputs folder)",
            "(Genomes Download) Download genomes from NCBI datasets",
            "(Genomes Unzip) Unzip genomes downloaded from NCBI datasets",
            "(Genomes Move) Move genomes to data/genomes folder",
            "(MakeDB Individual) Generate BLAST Databases for all genomes",
            "(MakeDB Model) Generate BLAST Databases if you manually downloaded the FASTA files",
            "(Sequences Split) Split FASTA sequences files to reduce workload by genus/species",
            "(TBLASTN) Run tblastn to obtain nucleotide sequences and select the best hits",
            "(AUGUSTUS) Run AUGUSTUS to extract and process genomic regions and hint files",
            "(EXONERATE) Run EXONERATE to extract and process genomic regions ab initio (WARNING: HIGH CPU/MEMORY USAGE)",
            "(SCHEMA) Generate chromosome schema with marked regions of interest",
            "Note: This program is for personal use, no updates or support are granted",
            "For support or more info, contact me using the links below"
        };
        
        for (size_t i = 0; i < steps.size(); ++i) {
            auto* step_box = Gtk::make_managed<Gtk::Box>(Gtk::ORIENTATION_HORIZONTAL, 5);
            step_box->set_margin_start(10);
            step_box->set_margin_bottom(5);
            
            auto* number_label = Gtk::make_managed<Gtk::Label>(std::to_string(i+1) + ".");
            number_label->set_xalign(0);
            
            auto* text_label = Gtk::make_managed<Gtk::Label>(steps[i]);
            text_label->set_xalign(0);
            text_label->set_line_wrap(true);
            text_label->set_max_width_chars(50);
            
            step_box->pack_start(*number_label, Gtk::PACK_SHRINK);
            step_box->pack_start(*text_label, Gtk::PACK_EXPAND_WIDGET);
            left_vbox.pack_start(*step_box, Gtk::PACK_SHRINK);
        }
        
        // Buttons spacing
        auto* space = Gtk::make_managed<Gtk::Label>("");
        space->set_margin_top(10);
        left_vbox.pack_start(*space, Gtk::PACK_SHRINK);

        // Cancel Button
        cancel_button = Gtk::make_managed<Gtk::Button>("Cancel Running Process");
        cancel_button->signal_clicked().connect(sigc::mem_fun(*this, &AppWindow::cancel_current_process));
        cancel_button->set_sensitive(false);
        left_vbox.pack_start(*cancel_button, Gtk::PACK_SHRINK);

        // Status indicator
        status_label = Gtk::make_managed<Gtk::Label>("Idle");
        status_label->set_margin_top(5);
        status_label->set_margin_bottom(10);
        left_vbox.pack_start(*status_label, Gtk::PACK_SHRINK);

        // Scripts buttons
        for (const auto& pair : script_buttons) {
            auto* btn = Gtk::make_managed<Gtk::Button>(pair.second);
            all_buttons.push_back(btn);
            btn->signal_clicked().connect(sigc::bind(
                sigc::mem_fun(*this, &AppWindow::on_script_button_clicked), 
                pair.first, btn));
            left_vbox.pack_start(*btn, Gtk::PACK_SHRINK);
        }
        
        // Footer
        auto* footer_box = Gtk::make_managed<Gtk::Box>(Gtk::ORIENTATION_VERTICAL);
        footer_box->set_margin_top(20);
        
        auto* developed_by = Gtk::make_managed<Gtk::Label>("Developed by Pedro Carvalho");
        developed_by->set_halign(Gtk::ALIGN_CENTER);
        
        Pango::FontDescription small_font;
        small_font.set_size(10 * PANGO_SCALE);
        developed_by->override_font(small_font);
        
        auto* github_link = Gtk::make_managed<Gtk::LinkButton>("https://github.com/capuccino26/PTPP.git", "Github Repository");
        github_link->set_halign(Gtk::ALIGN_CENTER);
        github_link->override_font(small_font);
        
        auto* linktree_link = Gtk::make_managed<Gtk::LinkButton>("https://linktr.ee/carvalhopc", "Linktree");
        linktree_link->set_halign(Gtk::ALIGN_CENTER);
        linktree_link->override_font(small_font);
        
        footer_box->pack_start(*developed_by, Gtk::PACK_SHRINK);
        footer_box->pack_start(*github_link, Gtk::PACK_SHRINK);
        footer_box->pack_start(*linktree_link, Gtk::PACK_SHRINK);
        
        left_vbox.pack_start(*footer_box, Gtk::PACK_SHRINK);

        show_all_children();
    }

    ~AppWindow() {
        cancel_current_process();
        if (command_thread.joinable()) {
            command_thread.join();
        }
    }

protected:
    void on_script_button_clicked(const std::string& script_name, Gtk::Button* clicked_button) {
        if (m_is_running) {
            return;
        }

        // Clean buffer
        output_view.get_buffer()->set_text("Starting process...\n");

        // Deactivate all buttons and set Cancel Button
        for (auto* btn : all_buttons) {
            btn->set_sensitive(false);
        }
        cancel_button->set_sensitive(true);
        status_label->set_text("Running: " + script_name);

        m_is_running = true;

        // Start Thread
        if (command_thread.joinable()) {
            command_thread.join();
        }

        command_thread = std::thread([this, script_name]() {
            run_command(script_name, script_name);
            
            // Update interface with main thread
            Glib::signal_idle().connect_once([this]() {
                m_is_running = false;
                for (auto* btn : all_buttons) {
                    btn->set_sensitive(true);
                }
                cancel_button->set_sensitive(false);
                status_label->set_text("Idle");
            });
        });
    }

    void cancel_current_process() {
        if (!m_is_running) {
            return;
        }

        m_cancelled = true;
        output_view.get_buffer()->insert_at_cursor("\n*** Cancelling process... ***\n");
    }

    void run_command(const std::string& cmd, const std::string& script_name) {
        m_cancelled = false;
        
        std::stringstream result;
        const size_t buffer_size = 1024;
        std::array<char, buffer_size> buffer;

        auto start_time = std::chrono::system_clock::now();
        std::time_t start_c = std::chrono::system_clock::to_time_t(start_time);

        // Register log
        std::ofstream log_file("log.txt", std::ios::app);
        if (log_file.is_open()) {
            log_file << "===============================================\n";
            log_file << "📅 Start: " << std::put_time(std::localtime(&start_c), "%Y-%m-%d %H:%M:%S") << "\n";
            log_file << "⚙️  Command: " << cmd << "\n";
            log_file << "📝 Script: " << script_name << "\n\n";
            log_file.flush();
        }

        std::string modified_cmd;
        if (script_name.ends_with(".py")) {
            modified_cmd = "bash -i -c 'conda activate PTPP && python -u bin/" + script_name + " 2>&1'";
        } else if (script_name.ends_with(".sh")) {
            modified_cmd = "bash bin/" + script_name + " 2>&1";
        }

        // Output command
        std::string info_msg = "Executing: " + modified_cmd + "\n\n";
        Glib::signal_idle().connect_once([this, info_msg]() {
            output_view.get_buffer()->insert(output_view.get_buffer()->end(), info_msg);
        });

        // Start process
        FILE* pipe = popen(modified_cmd.c_str(), "r");
        if (!pipe) {
            std::string error_msg = "❌ Error executing: " + modified_cmd + "\n";
            Glib::signal_idle().connect_once([this, error_msg]() {
                output_view.get_buffer()->set_text(error_msg);
            });
            
            if (log_file.is_open()) {
                log_file << error_msg;
                log_file << "⏱️  Duration: 0s (failed)\n";
                log_file << "===============================================\n\n";
                log_file.close();
            }
            return;
        }

        // Process output in chunks
        while (!m_cancelled && fgets(buffer.data(), buffer_size, pipe) != nullptr) {
            std::string line(buffer.data());
            
            // Write log
            if (log_file.is_open()) {
                log_file << line;
                log_file.flush();
            }
            
            // Update interface
            Glib::signal_idle().connect_once([this, line]() {
                auto buffer = output_view.get_buffer();
                buffer->insert(buffer->end(), line);
                
                // Auto-scroll interface
                auto mark = buffer->create_mark("end", buffer->get_iter_at_line(buffer->get_line_count()), false);
                output_view.scroll_to(mark);
                buffer->delete_mark(mark);
            });
            
            // Timeout for interface response
            Glib::MainContext::get_default()->iteration(false);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }

        // Finish process
        int status = pclose(pipe);
        auto end_time = std::chrono::system_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::seconds>(end_time - start_time).count();

        // Register log
        if (log_file.is_open()) {
            log_file << "\n";
            if (m_cancelled) {
                log_file << "⚠️ Process cancelled by user\n";
            } else if (status != 0) {
                log_file << "❌ Process completed with errors (status: " << status << ")\n";
            } else {
                log_file << "✅ Process completed successfully\n";
            }
            log_file << "⏱️  Duration: " << duration << "s\n";
            log_file << "===============================================\n\n";
            log_file.close();
        }

        // Update status interface
        std::string status_msg;
        if (m_cancelled) {
            status_msg = "\n\n*** Process was cancelled by user ***\n";
        } else if (status != 0) {
            status_msg = "\n\n*** Process completed with errors (status: " + std::to_string(status) + ") ***\n";
        } else {
            status_msg = "\n\n*** Process completed successfully ***\n";
        }
        status_msg += "Duration: " + std::to_string(duration) + "s\n";

        Glib::signal_idle().connect_once([this, status_msg]() {
            auto buffer = output_view.get_buffer();
            buffer->insert(buffer->end(), status_msg);
            
            // Auto-roll interface
            auto mark = buffer->create_mark(buffer->get_iter_at_line(buffer->get_line_count()), true);
            output_view.scroll_to(mark);
            buffer->delete_mark(mark);
        });
    }

private:
    // Main layout
    Gtk::Paned main_paned{Gtk::ORIENTATION_HORIZONTAL};
    Gtk::ScrolledWindow left_scroll;
    Gtk::ScrolledWindow right_scroll;
    Gtk::Box left_vbox{Gtk::ORIENTATION_VERTICAL};
    Gtk::TextView output_view;
    Gtk::Button* cancel_button;
    Gtk::Label* status_label;
    
    std::vector<std::pair<std::string, std::string>> script_buttons;
    std::vector<Gtk::Button*> all_buttons;
    
    // Thread handling
    std::thread command_thread;
    std::atomic<bool> m_is_running;
    std::atomic<bool> m_cancelled;
};

int main(int argc, char *argv[]) {
    auto app = Gtk::Application::create(argc, argv, "com.gene.structure.app");
    AppWindow window;
    return app->run(window);
}

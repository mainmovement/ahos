# AHOS GUI Launcher
# Creates a simple graphical interface for launching AHOS Portable

Add-Type -TypeDefinition @"
using System;
using System.Windows.Forms;
using System.Diagnostics;
using System.IO;

public class AHOSLauncher {
    public static void Main() {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new MainForm());
    }

    public class MainForm : Form {
        private Button launchBtn;
        private Button healthBtn;
        private Button readmeBtn;
        private Button configBtn;
        private TextBox outputBox;
        private string scriptDir;

        public MainForm() {
            scriptDir = Path.GetDirectoryName(Application.ExecutablePath);
            InitializeComponents();
        }

        private void InitializeComponents() {
            this.Text = "AHOS Portable Launcher";
            this.Size = new System.Drawing.Size(500, 400);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.MaximizeBox = false;

            // Title label
            titleLabel = new Label();
            titleLabel.Text = "AHOS Portable";
            titleLabel.Font = new System.Drawing.Font("Arial", 16, System.Drawing.FontStyle.Bold);
            titleLabel.TextAlign = ContentAlignment.MiddleCenter;
            titleLabel.Location = new System.Drawing.Point(150, 20);
            titleLabel.Size = new System.Drawing.Size(200, 30);

            // Launch button
            launchBtn = new Button();
            launchBtn.Text = "Launch AHOS";
            launchBtn.Font = new System.Drawing.Font("Arial", 10, System.Drawing.FontStyle.Bold);
            launchBtn.BackColor = System.Drawing.Color.DarkGreen;
            launchBtn.ForeColor = System.Drawing.Color.White;
            launchBtn.Location = new System.Drawing.Point(50, 70);
            launchBtn.Size = new System.Drawing.Size(180, 40);
            launchBtn.Click += new EventHandler(LaunchAHOS_Click);

            // Health button
            healthBtn = new Button();
            healthBtn.Text = "Health Check";
            healthBtn.Font = new System.Drawing.Font("Arial", 10);
            healthBtn.Location = new System.Drawing.Point(270, 70);
            healthBtn.Size = new System.Drawing.Size(180, 40);
            healthBtn.Click += new EventHandler(HealthCheck_Click);

            // Readme button
            readmeBtn = new Button();
            readmeBtn.Text = "Documentation";
            readmeBtn.Font = new System.Drawing.Font("Arial", 10);
            readmeBtn.Location = new System.Drawing.Point(50, 120);
            readmeBtn.Size = new System.Drawing.Size(180, 40);
            readmeBtn.Click += new EventHandler(Readme_Click);

            // Config button
            configBtn = new Button();
            configBtn.Text = "Configure API Keys";
            configBtn.Font = new System.Drawing.Font("Arial", 10);
            configBtn.Location = new System.Drawing.Point(270, 120);
            configBtn.Size = new System.Drawing.Size(180, 40);
            configBtn.Click += new EventHandler(Config_Click);

            // Output text box
            outputBox = new TextBox();
            outputBox.Multiline = true;
            outputBox.ScrollBars = ScrollBars.Vertical;
            outputBox.ReadOnly = true;
            outputBox.BackColor = System.Drawing.SystemColors.Control;
            outputBox.Location = new System.Drawing.Point(20, 180);
            outputBox.Size = new System.Drawing.Size(460, 180);

            // Add controls
            this.Controls.Add(titleLabel);
            this.Controls.Add(launchBtn);
            this.Controls.Add(healthBtn);
            this.Controls.Add(readmeBtn);
            this.Controls.Add(configBtn);
            this.Controls.Add(outputBox);

            // Initial status
            UpdateStatus("Ready to launch AHOS");
        }

        private Label titleLabel;

        private void LaunchAHOS_Click(object sender, EventArgs e) {
            UpdateStatus("Launching AHOS...");

            try {
                ProcessStartInfo startInfo = new ProcessStartInfo();
                startInfo.FileName = "powershell.exe";
                startInfo.Arguments = "-ExecutionPolicy Bypass -File \"ahos_launcher.ps1\"";
                startInfo.WorkingDirectory = scriptDir;
                startInfo.UseShellExecute = false;
                startInfo.CreateNoWindow = true;

                Process process = new Process();
                process.StartInfo = startInfo;
                process.Start();

                UpdateStatus("AHOS is starting...");

                // Open browser after 10 seconds
                System.Threading.Timer timer = new System.Threading.Timer((s) => {
                    try {
                        Process.Start("http://localhost:3000");
                    } catch (Exception ex) {
                        UpdateStatus("Could not open browser: " + ex.Message);
                    }
                }, null, 10000, System.Threading.Timeout.Infinite);

            } catch (Exception ex) {
                UpdateStatus("Error launching AHOS: " + ex.Message);
            }
        }

        private void HealthCheck_Click(object sender, EventArgs e) {
            UpdateStatus("Running health check...");

            try {
                ProcessStartInfo startInfo = new ProcessStartInfo();
                startInfo.FileName = "powershell.exe";
                startInfo.Arguments = "-ExecutionPolicy Bypass -File \"HEALTH_CHECK.ps1\"";
                startInfo.WorkingDirectory = scriptDir;
                startInfo.UseShellExecute = false;
                startInfo.RedirectStandardOutput = true;
                startInfo.RedirectStandardError = true;
                startInfo.CreateNoWindow = true;

                Process process = new Process();
                process.StartInfo = startInfo;
                process.Start();

                string output = process.StandardOutput.ReadToEnd();
                string error = process.StandardError.ReadToEnd();
                process.WaitForExit();

                UpdateStatus("Health Check Results:");
                UpdateStatus(output);
                if (!string.IsNullOrEmpty(error)) {
                    UpdateStatus("Errors: " + error);
                }

            } catch (Exception ex) {
                UpdateStatus("Error running health check: " + ex.Message);
            }
        }

        private void Readme_Click(object sender, EventArgs e) {
            try {
                string readmePath = Path.Combine(scriptDir, "README.md");
                if (File.Exists(readmePath)) {
                    Process.Start("notepad.exe", readmePath);
                } else {
                    UpdateStatus("README.md not found");
                }
            } catch (Exception ex) {
                UpdateStatus("Error opening README: " + ex.Message);
            }
        }

        private void Config_Click(object sender, EventArgs e) {
            try {
                // Open Credential Manager
                ProcessStartInfo startInfo = new ProcessStartInfo();
                startInfo.FileName = "cmd.exe";
                startInfo.Arguments = "/c start ms-settings:credentials";
                startInfo.UseShellExecute = false;
                startInfo.CreateNoWindow = true;

                Process.Start(startInfo);

                UpdateStatus("Opening Credential Manager...");
                UpdateStatus("Please add your API keys under 'Windows Credentials'");
                UpdateStatus("Look for entries starting with 'AHOS/'");

            } catch (Exception ex) {
                UpdateStatus("Error opening Credential Manager: " + ex.Message);
            }
        }

        private void UpdateStatus(string message) {
            if (outputBox.InvokeRequired) {
                outputBox.Invoke(new Action<string>(UpdateStatus), message);
            } else {
                outputBox.AppendText(message + Environment.NewLine);
                outputBox.ScrollToCaret();
            }
        }
    }
}
"@

# Run the GUI application
[AHOSLauncher]::Main()
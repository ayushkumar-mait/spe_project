import hudson.plugins.git.GitSCM
import hudson.triggers.SCMTrigger
import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition
import org.jenkinsci.plugins.workflow.job.WorkflowJob

def jenkins = Jenkins.get()
def jobName = "automated-chaos-platform"
def repoUrl = System.getenv("PROJECT_REPO_URL") ?: "https://github.com/ayushkumar-mait/spe_project.git"

def job = jenkins.getItem(jobName)
if (job == null) {
  job = jenkins.createProject(WorkflowJob, jobName)
}

def scm = new GitSCM(repoUrl)
def definition = new CpsScmFlowDefinition(scm, "Jenkinsfile")
definition.setLightweight(false)
job.setDefinition(definition)

// GitHub webhook and pollSCM are declared in Jenkinsfile. This job-level trigger
// is a laptop-friendly fallback, and the map prevents duplicate SCM triggers.
if (!job.getTriggers().values().any { it instanceof SCMTrigger }) {
  job.addTrigger(new SCMTrigger("H/2 * * * *"))
}

job.save()
println("Seeded/updated Jenkins pipeline job '${jobName}' from ${repoUrl}")

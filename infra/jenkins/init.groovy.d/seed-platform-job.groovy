import hudson.plugins.git.GitSCM
import hudson.triggers.SCMTrigger
import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition
import org.jenkinsci.plugins.workflow.job.WorkflowJob

def jenkins = Jenkins.get()
def jobName = "automated-chaos-platform"
def repoUrl = System.getenv("PROJECT_REPO_URL") ?: "file:///workspace/project"

if (jenkins.getItem(jobName) == null) {
  def job = jenkins.createProject(WorkflowJob, jobName)
  def scm = new GitSCM(repoUrl)
  def definition = new CpsScmFlowDefinition(scm, "Jenkinsfile")
  definition.setLightweight(false)
  job.setDefinition(definition)

  // Local fallback trigger. GitHub webhook trigger is declared inside Jenkinsfile.
  job.addTrigger(new SCMTrigger("H/2 * * * *"))
  job.save()
  println("Seeded Jenkins pipeline job '${jobName}' from ${repoUrl}")
}


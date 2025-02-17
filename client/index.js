const fullStar = "★";
const emptyStar = "☆";

const commitFragment = `
fragment commitFragment on Repository {
  ref(qualifiedName: "master") {
    target {
      ... on Commit {
        history {
          totalCount
        }
      }
    }
  }
}
`;

const queryRepoList = `
{
  viewer {
    name
    repositories (first: 12,
      orderBy: {field: CREATED_AT, direction: DESC}
    ) {
      totalCount
      nodes {
        name
        openIssues: issues (states: OPEN) {
          totalCount
        }
        openPRs: pullRequests(states: OPEN) {
          totalCount
        }
        ... commitFragment
        viewerHasStarred
        id
      }
    }
  }
}
` + commitFragment;

let mutationAddStar = `
mutation addStar ($repoId: ID!) {
  addStar (input: {starrableId: $repoId}) {
    repo: starrable {
      ... on Repository {
        name
        viewerHasStarred
      }
    }
  }
}`;

let mutationRemoveStar = `
mutation removeStar ($repoId: ID!) {
  removeStar (input: {starrableId: $repoId}) {
    repo: starrable {
      ... on Repository {
        name
        viewerHasStarred
      }
    }
  }
}`;

function gqlRequest(query, variables, onSuccess) {
  // MAKE GRAPHQL REQUEST
  $.post({
    url: "https://api.github.com/graphql",
    contentType: "application/json",
    headers: {
      Authorization: `bearer ${env.GITHUB_PERSONAL_ACCESS_TOKEN}`
    },
    data: JSON.stringify({
      query: query,
      variables: variables
    }),
    success: (response) => {
      if (response.errors) {
        console.log(response.errors);
      } else {
        onSuccess(response.data);
      }
    }
  });
}

function resetStar(starElement, viewerHasStarred) {
  starElement.innerText =
    viewerHasStarred ? fullStar : emptyStar;
}

function starHandler(element) {
  // STAR OR UNSTAR REPO BASED ON ELEMENT STATE
  let mutation = mutationAddStar
  let mutationKey = 'addStar'
  if (element.innerText === fullStar) {
    mutation = mutationRemoveStar
    mutationKey = 'removeStar'
  }

  gqlRequest(mutation, {repoId: element.id}, (data) => {
    console.log(data);
    resetStar(element, data[mutationKey].repo.viewerHasStarred);
  })
}

$(window).ready(function() {
  // GET NAME AND REPOSITORIES FOR VIEWER
  gqlRequest(queryRepoList, {}, (data) => {
    $('header h2').text(`Hello ${data.viewer.name}`);
    console.log(data);
    const repos = data.viewer.repositories;
    if (repos.totalCount > 0) {
      $('ul.repos').empty();
      repos.nodes.forEach((repo) => {
        const star = repo.viewerHasStarred ? fullStar : emptyStar;
        const card = `<li>
        <h3>
          ${repo.name}
          <span class="star" id=${repo.id} onClick="starHandler(this)">${star}</span>
        </h3>
        <p>${repo.openIssues.totalCount} open issues</p>
        <p>${repo.openPRs.totalCount} open PRs</p>
        <p>${repo.ref.target.history.totalCount} commits</p>
        </li>`;
        $('ul.repos').append(card);
      })
    }
  });
});

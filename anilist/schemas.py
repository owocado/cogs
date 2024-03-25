CHARACTER_SCHEMA = """
query ($page: Int, $perPage: Int, $search: String, $sort: [MediaSort], $onList: Boolean, $withRoles: Boolean = false) {
  Page(page: $page, perPage: $perPage) {
    characters(search: $search, sort: FAVOURITES_DESC) {
      age
      dateOfBirth {
        day
        month
        year
      }
      description(asHtml: false)
      gender
      image {
        large
      }
      name {
        full
        native
        userPreferred
        alternative
      }
      siteUrl
      media(page: $page, sort: $sort, onList: $onList) @include(if: $withRoles) {
        pageInfo {
          total
          perPage
          currentPage
          lastPage
          hasNextPage
        }
        edges {
          characterRole
          node {
            type
            isAdult
            siteUrl
            title {
              userPreferred
            }
            startDate {
              year
            }
          }
        }
      }
    }
  }
}
"""


GENRE_COLLECTION_SCHEMA = """
query {
  GenreCollection
}
"""


GENRE_SCHEMA = """
query ($page: Int, $perPage: Int, $genre: String, $type: MediaType, $format_in: [MediaFormat]) {
  Page(page: $page, perPage: $perPage) {
    media(genre: $genre, type: $type, format_in: $format_in) {
      id
      idMal
      title {
        english
        native
        romaji
      }
      coverImage {
        large
        color
      }
      description
      bannerImage
      format
      status
      type
      meanScore
      startDate {
        day
        month
        year
      }
      endDate {
        day
        month
        year
      }
      duration
      source
      episodes
      chapters
      volumes
      studios {
        nodes {
          name
        }
      }
      synonyms
      genres
      trailer {
        id
        site
      }
      externalLinks {
        site
        url
      }
      siteUrl
      isAdult
      nextAiringEpisode {
        episode
        airingAt
      }
    }
  }
}
"""


MEDIA_SCHEMA = """
query ($page: Int, $perPage: Int, $search: String, $type: MediaType, $sort: [MediaSort]) {
  Page(page: $page, perPage: $perPage) {
    media(search: $search, type: $type, sort: $sort) {
      id
      idMal
      title {
        english
        native
        romaji
      }
      coverImage {
        large
        color
      }
      description
      bannerImage
      format
      status
      type
      meanScore
      startDate {
        day
        month
        year
      }
      endDate {
        day
        month
        year
      }
      duration
      source
      episodes
      chapters
      volumes
      studios {
        nodes {
          name
        }
      }
      synonyms
      genres
      trailer {
        id
        site
      }
      externalLinks {
        site
        url
      }
      siteUrl
      isAdult
      nextAiringEpisode {
        episode
        airingAt
      }
    }
  }
}
"""


SCHEDULE_SCHEMA = """
query ($page: Int, $perPage: Int, $notYetAired: Boolean, $sort: [AiringSort]) {
  Page(page: $page, perPage: $perPage) {
    airingSchedules(notYetAired: $notYetAired, sort: $sort) {
      airingAt
      episode
      media {
        duration
        format
        idMal
        isAdult
        siteUrl
        title {
          romaji
          english
        }
        coverImage {
          large
        }
        externalLinks {
          site
          url
        }
        trailer {
          id
          site
        }
      }
    }
  }
}
"""


STAFF_SCHEMA = """
query ($page: Int, $perPage: Int, $search: String) {
  Page(page: $page, perPage: $perPage) {
    staff(search: $search, sort: FAVOURITES_DESC) {
      name {
        full
        native
        userPreferred
        alternative
      }
      image {
        large
      }
      description(asHtml: false)
      siteUrl
      age
      gender
      yearsActive
      homeTown
      primaryOccupations
      dateOfBirth {
        day
        month
        year
      }
      dateOfDeath {
        day
        month
        year
      }
      language: languageV2
      characterMedia(page: 1, sort: POPULARITY_DESC) {
        edges {
          characterRole
          node {
            type
            isAdult
            title {
              userPreferred
            }
            siteUrl
            startDate {
              year
            }
          }
          characters {
            name {
              userPreferred
            }
            siteUrl
          }
        }
        pageInfo {
          total
          perPage
          currentPage
          lastPage
          hasNextPage
        }
      }
    }
  }
}
"""


STUDIO_SCHEMA = """
query ($page: Int, $perPage: Int, $search: String) {
  Page(page: $page, perPage: $perPage) {
    studios(search: $search) {
      name
      favourites
      isAnimationStudio
      siteUrl
      media(sort: POPULARITY_DESC, perPage: 30) {
        nodes {
          episodes
          format
          isAdult
          siteUrl
          status
          title {
            english
            romaji
          }
        }
      }
    }
  }
}
"""


TAG_COLLECTION_SCHEMA = """
query {
  MediaTagCollection {
    name
    description
    isAdult
  }
}
"""


TAG_SCHEMA = """
query ($page: Int, $perPage: Int, $tag: String, $type: MediaType, $format_in: [MediaFormat]) {
  Page(page: $page, perPage: $perPage) {
    media(tag: $tag, type: $type, format_in: $format_in) {
      id
      idMal
      title {
        romaji
        english
      }
      coverImage {
        large
        color
      }
      description
      bannerImage
      format
      status
      type
      meanScore
      startDate {
        day
        month
        year
      }
      endDate {
        day
        month
        year
      }
      duration
      source
      episodes
      chapters
      volumes
      studios {
        nodes {
          name
        }
      }
      synonyms
      genres
      trailer {
        id
        site
      }
      externalLinks {
        site
        url
      }
      siteUrl
      isAdult
      nextAiringEpisode {
        episode
        airingAt
      }
    }
  }
}
"""


USER_SCHEMA = """
query ($page: Int, $perPage: Int, $search: String) {
  Page(page: $page, perPage: $perPage) {
    users(search: $search) {
      id
      name
      about(asHtml: false)
      donatorTier
      createdAt
      updatedAt
      avatar {
        large
      }
      bannerImage
      siteUrl
      previousNames {
        name
        createdAt
        updatedAt
      }
      statistics {
        anime {
          count
          meanScore
          minutesWatched
          episodesWatched
        }
        manga {
          count
          meanScore
          chaptersRead
          volumesRead
        }
      }
    }
  }
}
"""

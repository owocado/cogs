CHARACTER_SCHEMA = """
query ($page: Int, $perPage: Int, $search: String, $sort: [CharacterSort]) {
  Page(page: $page, perPage: $perPage) {
    characters(search: $search, sort: $sort) {
      name {
        full
        native
        alternative
      }
      image {
        large
      }
      description(asHtml: false)
      gender
      dateOfBirth {
        year
        month
        day
      }
      age
      siteUrl
      media(perPage: 10) {
        nodes {
          siteUrl
          type
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


GENRE_SCHEMA = """
query ($page: Int, $perPage: Int, $genre: String, $type: MediaType, $format_in: [MediaFormat]) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      lastPage
    }
    media(genre: $genre, type: $type, format_in: $format_in) {
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
        year
        month
        day
      }
      endDate {
        year
        month
        day
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
        timeUntilAiring
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
        year
        month
        day
      }
      endDate {
        year
        month
        day
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
        timeUntilAiring
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
      timeUntilAiring
      airingAt
      episode
      media {
        id
        idMal
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
        duration
        format
        isAdult
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
    staff(search: $search) {
      name {
        full
        native
      }
      language
      image {
        large
      }
      description
      siteUrl
      staffMedia(perPage: 10) {
        nodes {
          siteUrl
          title {
            romaji
          }
        }
      }
      characters(perPage: 10) {
        nodes {
          id
          siteUrl
          name {
            full
          }
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
      media(sort: POPULARITY_DESC, perPage: 30) {
        nodes {
          siteUrl
          title {
            romaji
          }
          format
          episodes
          coverImage {
            large
          }
        }
      }
      isAnimationStudio
      siteUrl
    }
  }
}
"""


TAG_SCHEMA = """
query ($page: Int, $perPage: Int, $tag: String, $type: MediaType, $format_in: [MediaFormat]) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      lastPage
    }
    media(tag: $tag, type: $type, format_in: $format_in) {
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
        year
        month
        day
      }
      endDate {
        year
        month
        day
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
        timeUntilAiring
      }
    }
  }
}
"""


TRENDING_SCHEMA = """
query ($page: Int, $perPage: Int, $type: MediaType, $sort: [MediaSort]) {
  Page(page: $page, perPage: $perPage) {
    media(type: $type, sort: $sort) {
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
        year
        month
        day
      }
      endDate {
        year
        month
        day
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
        timeUntilAiring
        airingAt
      }
    }
  }
}
"""


USER_SCHEMA = """
query ($page: Int, $perPage: Int, $name: String) {
  Page(page: $page, perPage: $perPage) {
    users(name: $name) {
      name
      avatar {
        large
        medium
      }
      about
      bannerImage
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
      favourites {
        anime {
          nodes {
            id
            siteUrl
            title {
              romaji
              english
              native
              userPreferred
            }
          }
        }
        manga {
          nodes {
            id
            siteUrl
            title {
              romaji
              english
              native
              userPreferred
            }
          }
        }
        characters {
          nodes {
            id
            siteUrl
            name {
              first
              last
              full
              native
            }
          }
        }
        staff {
          nodes {
            id
            siteUrl
            name {
              first
              last
              full
              native
            }
          }
        }
        studios {
          nodes {
            id
            siteUrl
            name
          }
        }
      }
      siteUrl
    }
  }
}
"""
